#!/usr/bin/env python3
"""
Script pour exécuter les tests du projet Elections Backend
"""
import subprocess
import sys
import os

def run_tests():
    """Exécute la suite de tests"""

    print("🧪 Lancement des tests unitaires et d'intégration...")
    print("=" * 60)

    # Commandes de test
    commands = [
        # Tests unitaires uniquement
        ["pytest", "tests/unit/", "-v", "--tb=short"],

        # Tests d'intégration
        ["pytest", "tests/integration/", "-v", "--tb=short"],

        # Tous les tests avec couverture
        ["pytest", "tests/", "--cov=.", "--cov-report=term-missing", "--cov-report=html"]
    ]

    for i, cmd in enumerate(commands, 1):
        print(f"\n🔧 Étape {i}/{len(commands)}: {' '.join(cmd)}")
        print("-" * 40)

        try:
            result = subprocess.run(cmd, check=False, capture_output=False)
            if result.returncode != 0:
                print(f"⚠️  Des tests ont échoué dans l'étape {i}")
            else:
                print(f"✅ Étape {i} réussie")
        except subprocess.SubprocessError as e:
            print(f"❌ Erreur lors de l'exécution: {e}")
            return False

    print("\n" + "=" * 60)
    print("🎯 Tests terminés ! Consultez les rapports générés.")
    print("📊 Rapport de couverture HTML: htmlcov/index.html")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)