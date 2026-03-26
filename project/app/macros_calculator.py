def calculate_macros(age, gender, weight, height, activity, goal):
    """Calcule le métabolisme de base (Mifflin-St Jeor) et tous les macros."""
    # 1. Calcul BMR
    if gender == 'homme':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # 2. Multiplicateur d'activité
    activity_multipliers = {
        'sédentaire': 1.2, 
        'léger': 1.375, 
        'modéré': 1.55, 
        'intense': 1.725
    }
    tdee = bmr * activity_multipliers.get(activity, 1.2)
    
    # 3. Ajustement selon l'objectif et répartition
    if goal == 'perte':
        target_calories = tdee - 500
        protein = weight * 2.2      # Protéines hautes en déficit
        fat_percentage = 0.25       # 25% de lipides
    elif goal == 'masse':
        target_calories = tdee + 500
        protein = weight * 2.0
        fat_percentage = 0.25       # Garder les graisses modérées, monter les glucides
    else:
        target_calories = tdee
        protein = weight * 1.8
        fat_percentage = 0.30       # 30% de lipides pour l'équilibre
        
    # 4. Calcul des Lipides (Fats) : 1g = 9 kcal
    fat_calories = target_calories * fat_percentage
    fat = fat_calories / 9
    
    # 5. Calcul des Glucides (Carbs) : 1g = 4 kcal
    protein_calories = protein * 4
    carb_calories = target_calories - protein_calories - fat_calories
    
    # Sécurité au cas où les calories seraient trop basses
    carb = max(0, carb_calories / 4)
        
    return int(target_calories), int(protein), int(carb), int(fat)