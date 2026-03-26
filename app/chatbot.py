import os
from langchain.agents import create_agent
from langchain_openai import AzureOpenAIEmbeddings, ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

def get_embeddings_endpoint():
    endpoint = os.getenv("AI_ENDPOINT", "")
    return endpoint.replace("/openai/v1", "") if endpoint.endswith("/openai/v1") else endpoint

# ==========================================
# 1. INITIALISATION DES MODÈLES
# ==========================================
embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=get_embeddings_endpoint(),
    api_key=os.getenv("AI_API_KEY"),
    model=os.getenv("AI_EMBEDDING_MODEL", "text-embedding-ada-002"),
    api_version="2024-02-01",
)

model = ChatOpenAI(
    model=os.getenv("AI_MODEL"),
    base_url=os.getenv("AI_ENDPOINT"),
    api_key=os.getenv("AI_API_KEY")
)

# ==========================================
# 2. CRÉATION DES BASES DE DONNÉES (RAG)
# ==========================================
fitness_docs = [
    Document(page_content="Bench Press (Développé couché) : Exercice polyarticulaire ciblant les pectoraux, les triceps et les épaules. Équipement : Banc, Barre.", metadata={"muscle": "Chest", "type": "Strength"}),
    Document(page_content="Barbell Curl (Curl à la barre) : Exercice d'isolation ciblant les biceps. Équipement : Barre. 3 séries de 10-12 répétitions recommandées pour l'hypertrophie.", metadata={"muscle": "Biceps", "type": "Strength"}),
    Document(page_content="HIIT Treadmill (Tapis de course) : 30 secondes de sprint, 30 secondes de marche. Excellent pour la perte de graisse et l'endurance cardiovasculaire.", metadata={"muscle": "Full Body", "type": "Cardio"})
]

nutrition_docs = [
    Document(page_content="Recette : High Protein Chicken & Rice Bowl. Ingrédients : 200g de blanc de poulet, 100g de riz basmati, 50g de brocolis. Nutrition : 550 kcal, 45g de protéines, 55g de glucides, 10g de lipides.", metadata={"category": "High Protein", "calories": 550}),
    Document(page_content="Recette : Avocado Toast with Poached Eggs. Ingrédients : 2 tranches de pain complet, 1/2 avocat, 2 œufs. Nutrition : 420 kcal, 20g de protéines, 35g de glucides, 22g de lipides.", metadata={"category": "Balanced", "calories": 420}),
    Document(page_content="Recette : Vegan Lentil Stew. Ingrédients : 150g de lentilles corail, lait de coco, carottes, épices. Nutrition : 400 kcal, 18g de protéines, 60g de glucides, 15g de lipides.", metadata={"category": "Vegan", "calories": 400})
]

fitness_vector_store = InMemoryVectorStore.from_documents(fitness_docs, embeddings)
nutrition_vector_store = InMemoryVectorStore.from_documents(nutrition_docs, embeddings)

# ==========================================
# 3. OUTILS ET AGENTS
# ==========================================
@tool
def search_fitness_database(query: str) -> str:
    """Search the Mega Fitness Database to find specific exercises, target muscles, and workout equipment."""
    results = fitness_vector_store.similarity_search(query, k=2)
    return "\n\n".join([f"[{doc.metadata['muscle']}]: {doc.page_content}" for doc in results])

@tool
def search_nutrition_database(query: str) -> str:
    """Search the Food.com Recipes Database to find meals, exact ingredients, and nutritional values."""
    results = nutrition_vector_store.similarity_search(query, k=2)
    return "\n\n".join([f"[{doc.metadata['category']}]: {doc.page_content}" for doc in results])

fitness_agent = create_agent(
    model=model,
    tools=[search_fitness_database],
    system_prompt="Tu es un coach sportif expert. Construis UNIQUEMENT le plan d'entraînement. Ne donne AUCUN conseil en nutrition, un diététicien s'en chargera après toi."
)

nutrition_agent = create_agent(
    model=model,
    tools=[search_nutrition_database],
    system_prompt="Tu es un diététicien expert. Utilise ton outil de recherche pour générer un plan de repas (Meal Plan) avec des recettes précises et des macros adaptés pour soutenir l'entraînement."
)

# ==========================================
# 4. LA FONCTION EXPOSÉE POUR LE WEB
# ==========================================
def generate_ai_plans(user_profile: str, meals_count: int) -> tuple[str, str]:
    """Exécute la chaîne d'agents et retourne le gym_plan et le meal_plan."""
    
    # 1. Le Coach génère le Gym Plan
    gym_response = fitness_agent.invoke({
        "messages": [HumanMessage(content=f"Crée un gym plan pour : {user_profile}")]
    })
    gym_plan = gym_response["messages"][-1].content
    
    # 2. Le Nutritionniste génère le Meal Plan avec le contexte du sport
    nutrition_prompt = f"{user_profile}\n\nProgramme sportif prévu :\n{gym_plan}\n\nGénère le plan alimentaire détaillé avec {meals_count} repas/jour."
    nutri_response = nutrition_agent.invoke({
        "messages": [HumanMessage(content=nutrition_prompt)]
    })
    meal_plan = nutri_response["messages"][-1].content
    
    return gym_plan, meal_plan