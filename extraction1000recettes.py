import pandas as pd

# 1. Lire le fichier
fichier_source = "C:/Users/DeezWit/Desktop/RAW_recipes.csv"
print("Chargement du fichier en cours...")
df = pd.read_csv(fichier_source)

# 2. Extraire 1000 lignes au hasard
print("Extraction de 1000 recettes au hasard...")
df_extrait = df.sample(n=1000, random_state=42)

# 3. Sauvegarder en CSV (C'est ici qu'on utilise to_csv au lieu de to_excel)
fichier_destination = "1000_recettes_extraites.csv"
df_extrait.to_csv(fichier_destination, index=False)

print(f"Succès ! Tes recettes sont dans : {fichier_destination}")
