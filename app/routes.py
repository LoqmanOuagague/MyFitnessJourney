from flask import Blueprint, render_template, request, jsonify
from app.macros_calculator import calculate_macros
from app.chatbot import generate_ai_plans

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/generate', methods=['POST'])
def generate_plans():
    data = request.json
    
    try:
        # 1. On récupère maintenant les 4 valeurs !
        calories, protein, carbs, fats = calculate_macros(
            int(data['age']), data['gender'], float(data['weight']), 
            float(data['height']), data['activity'], data['goal']
        )
        
        # 2. Le profil est ultra-précis pour l'Agent Nutritionniste
        user_profile = f"""
        Profil : {data['gender']}, {data['age']} ans, {data['weight']}kg, {data['height']}cm.
        Objectif : {data['goal']} focalisé sur {data['focus']}.
        Expérience : {data['experience']}. Lieu : {data['location']} ({data['days']} jours/semaine).
        Régime : {data['diet']}. Aversions : {data['allergies']}.
        CIBLE CALORIQUE : {calories} kcal/jour. 
        MACROS CIBLES : {protein}g Protéines, {carbs}g Glucides, {fats}g Lipides.
        """
        
        # 3. Génération IA
        gym_plan, meal_plan = generate_ai_plans(user_profile, int(data['meals']))
        
        # 4. Renvoi du JSON étendu au Frontend
        return jsonify({
            "gym_plan": gym_plan, 
            "meal_plan": meal_plan, 
            "calories": calories, 
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500