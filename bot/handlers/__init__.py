from . import food, profile

# Tartib muhim: profil (FSM) birinchi, food oxirida umumiy fallback bilan
routers = [profile.router, food.router]
