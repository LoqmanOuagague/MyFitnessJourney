import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import AzureOpenAIEmbeddings, ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# Chargement des variables d'environnement
load_dotenv()

def get_embeddings_endpoint():
    """Get the Azure OpenAI endpoint, removing /openai/v1 suffix if present."""
    endpoint = os.getenv("AI_ENDPOINT", "")
    if endpoint.endswith("/openai/v1"):
        endpoint = endpoint.replace("/openai/v1", "")
    return endpoint

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

# Dataset 1 : Mega Fitness Dataset (Kaggle) - Simulation
fitness_docs = [
    Document(page_content="Bench Press (Développé couché) : Exercice polyarticulaire ciblant les pectoraux, les triceps et les épaules. Équipement : Banc, Barre.", metadata={"muscle": "Chest", "type": "Strength"}),
    Document(page_content="Barbell Curl (Curl à la barre) : Exercice d'isolation ciblant les biceps. Équipement : Barre. 3 séries de 10-12 répétitions recommandées pour l'hypertrophie.", metadata={"muscle": "Biceps", "type": "Strength"}),
    Document(page_content="HIIT Treadmill (Tapis de course) : 30 secondes de sprint, 30 secondes de marche. Excellent pour la perte de graisse et l'endurance cardiovasculaire.", metadata={"muscle": "Full Body", "type": "Cardio"})
]

# Dataset 2 : Food.com Recipes Dataset (Kaggle) - Simulation
nutrition_docs = [
    Document(page_content="Recette : High Protein Chicken & Rice Bowl. Ingrédients : 200g de blanc de poulet, 100g de riz basmati, 50g de brocolis. Nutrition : 550 kcal, 45g de protéines, 55g de glucides, 10g de lipides.", metadata={"category": "High Protein", "calories": 550}),
    Document(page_content="Recette : Avocado Toast with Poached Eggs. Ingrédients : 2 tranches de pain complet, 1/2 avocat, 2 œufs. Nutrition : 420 kcal, 20g de protéines, 35g de glucides, 22g de lipides.", metadata={"category": "Balanced", "calories": 420}),
    Document(page_content="Recette : Vegan Lentil Stew. Ingrédients : 150g de lentilles corail, lait de coco, carottes, épices. Nutrition : 400 kcal, 18g de protéines, 60g de glucides, 15g de lipides.", metadata={"category": "Vegan", "calories": 400})
]

# Création des deux Vector Stores distincts
fitness_vector_store = InMemoryVectorStore.from_documents(fitness_docs, embeddings)
nutrition_vector_store = InMemoryVectorStore.from_documents(nutrition_docs, embeddings)

# ==========================================
# 3. CRÉATION DES OUTILS DE RECHERCHE (TOOLS)
# ==========================================

@tool
def search_fitness_database(query: str) -> str:
    """Search the Mega Fitness Database to find specific exercises, target muscles, and workout equipment.
    Use this to build the gym plan.
    """
    results = fitness_vector_store.similarity_search(query, k=2)
    return "\n\n".join([f"[{doc.metadata['muscle']}]: {doc.page_content}" for doc in results])

@tool
def search_nutrition_database(query: str) -> str:
    """Search the Food.com Recipes Database to find meals, exact ingredients, and nutritional values (macros/calories).
    Use this to build the meal plan.
    """
    results = nutrition_vector_store.similarity_search(query, k=2)
    return "\n\n".join([f"[{doc.metadata['category']}]: {doc.page_content}" for doc in results])

# ==========================================
# 4. DÉFINITION DES DEUX AGENTS
# ==========================================

# Agent 1 : Coach Sportif
fitness_agent = create_agent(
    model=model,
    tools=[search_fitness_database],
    system_prompt="Tu es un coach sportif expert. Utilise ton outil de recherche pour trouver des exercices précis dans la base de données (Mega Fitness) et construis un plan d'entraînement (Gym Plan) adapté aux objectifs de l'utilisateur."
)

# Agent 2 : Nutritionniste
nutrition_agent = create_agent(
    model=model,
    tools=[search_nutrition_database],
    system_prompt="Tu es un diététicien expert. On va te fournir le profil d'un utilisateur ET son plan d'entraînement. Utilise ton outil de recherche (Food.com Database) pour générer un plan de repas (Meal Plan) avec des recettes précises et des macros adaptés pour soutenir son entraînement."
)

def main():
    # Le formulaire rempli par l'utilisateur
    user_profile = "Je suis un homme de 75kg. Mon objectif est de prendre de la masse musculaire au niveau du haut du corps (pectoraux et biceps). J'aimerais aussi un plan alimentaire riche en protéines d'environ 2500 kcal."

    print("🏋️‍♂️ Démarrage de l'application Multi-Agents RAG...")
    print(f"\n📝 Profil utilisateur : {user_profile}")
    print("-" * 60)

    # ÉTAPE 1 : Le premier Agent crée le Gym Plan
    print("🤖 Agent 1 (Coach Sportif) réfléchit et cherche dans le Mega Fitness Dataset...")
    fitness_response = fitness_agent.invoke({
        "messages": [HumanMessage(content=f"Crée un gym plan pour ce profil : {user_profile}")]
    })
    
    gym_plan = fitness_response["messages"][-1].content
    print("\n✅ GYM PLAN GÉNÉRÉ :\n")
    print(gym_plan)
    print("=" * 60)

    # ÉTAPE 2 : On passe le Gym Plan et le profil au deuxième Agent pour le Meal Plan
    print("🤖 Agent 2 (Nutritionniste) réfléchit et cherche dans le Food.com Dataset...")
    
    # Prompt combiné : Profil + Gym Plan pour donner tout le contexte au nutritionniste
    nutrition_prompt = f"""
    Voici le profil de l'utilisateur : {user_profile}
    Voici le programme d'entraînement qu'il va suivre :
    {gym_plan}
    
    Génère un plan de repas adapté en cherchant des recettes riches en protéines dans ta base de données.
    """
    
    nutrition_response = nutrition_agent.invoke({
        "messages": [HumanMessage(content=nutrition_prompt)]
    })
    
    meal_plan = nutrition_response["messages"][-1].content
    print("\n🥗 MEAL PLAN GÉNÉRÉ :\n")
    print(meal_plan)
    print("=" * 60)

if __name__ == "__main__":
    main()