# ============================================
# SIMULATEUR DE COMPTE BANCAIRE - VERSION UNIQUE
# ============================================

from datetime import datetime
import json
import os

# ============================================
# PARTIE 1 : Classe Operation
# ============================================
class Operation:
    """Représente une opération bancaire avec date, type, montant et description"""
    
    def __init__(self, type_op, montant, description=""):
        self.date = datetime.now().isoformat()
        self.type = type_op
        self.montant = montant
        self.description = description
    
    def to_dict(self):
        return {
            "date": self.date,
            "type": self.type,
            "montant": self.montant,
            "description": self.description
        }
    
    @staticmethod
    def from_dict(data):
        op = Operation(data["type"], data["montant"], data.get("description", ""))
        op.date = data["date"]
        return op
    
    def __str__(self):
        signe = "+" if self.type == "depot" else "-"
        desc = f" - {self.description}" if self.description else ""
        return f"[{self.date[:10]}] {self.type.upper()}: {signe}{self.montant:.2f}€{desc}"


# ============================================
# PARTIE 2 : Classe CompteBancaire
# ============================================
class CompteBancaire:
    """Représente un compte bancaire avec solde et historique des opérations"""
    
    def __init__(self, numero, titulaire, solde_initial=0):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde_initial
        self.historique = []
        if solde_initial > 0:
            self.historique.append(Operation("depot", solde_initial, "Solde initial"))
    
    def deposer(self, montant):
        if montant <= 0:
            print(f"❌ Erreur: Le montant doit être positif")
            return False
        self.solde += montant
        self.historique.append(Operation("depot", montant))
        print(f"✅ Dépôt de {montant:.2f}€ effectué")
        return True
    
    def retirer(self, montant):
        if montant <= 0 or montant > self.solde:
            print(f"❌ Retrait impossible")
            return False
        self.solde -= montant
        self.historique.append(Operation("retrait", montant))
        print(f"✅ Retrait de {montant:.2f}€ effectué")
        return True
    
    def afficher_solde(self):
        print(f"💰 Compte {self.numero} - {self.titulaire} : {self.solde:.2f}€")
    
    def afficher_historique(self, nb_dernieres=None):
        ops = self.historique[-nb_dernieres:] if nb_dernieres else self.historique
        if not ops:
            print("Aucune opération enregistrée")
            return
        print(f"📊 Historique compte {self.numero}:")
        for op in ops:
            print(f"   {op}")
    
    def to_dict(self):
        return {
            "numero": self.numero,
            "titulaire": self.titulaire,
            "solde": self.solde,
            "historique": [op.to_dict() for op in self.historique]
        }
    
    @staticmethod
    def from_dict(data):
        compte = CompteBancaire(data["numero"], data["titulaire"], data["solde"])
        compte.historique = [Operation.from_dict(op) for op in data["historique"]]
        return compte
    
    def __str__(self):
        return f"{self.numero} - {self.titulaire}: {self.solde:.2f}€ ({len(self.historique)} ops)"


# ============================================
# PARTIE 3 : Classe Banque
# ============================================
class Banque:
    """Gère tous les comptes et opérations"""
    
    def __init__(self):
        self.comptes = {}
    
    def creer_compte(self, numero, titulaire, solde_initial=0):
        if numero in self.comptes:
            print(f"❌ Compte {numero} existe déjà")
            return None
        compte = CompteBancaire(numero, titulaire, solde_initial)
        self.comptes[numero] = compte
        print(f"✅ Compte {numero} créé pour {titulaire}")
        return compte
    
    def virement(self, src, dest, montant):
        if src not in self.comptes or dest not in self.comptes or src == dest:
            print("❌ Virement impossible")
            return False
        if self.comptes[src].retirer(montant):
            self.comptes[dest].deposer(montant)
            self.comptes[src].historique[-1].description = f"Virement vers {dest}"
            self.comptes[dest].historique[-1].description = f"Virement de {src}"
            print(f"✅ Virement de {montant:.2f}€ effectué de {src} vers {dest}")
            return True
        return False
    
    def lister_comptes(self):
        if not self.comptes:
            print("Aucun compte enregistré")
            return
        print("🏦 Liste des comptes:")
        for compte in self.comptes.values():
            print(f"   {compte}")
    
    def sauvegarder(self, fichier="banque.json"):
        data = {num: compte.to_dict() for num, compte in self.comptes.items()}
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Données sauvegardées dans {fichier}")
    
    def charger(self, fichier="banque.json"):
        if not os.path.exists(fichier):
            print("Fichier introuvable, banque vide")
            return
        with open(fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.comptes = {num: CompteBancaire.from_dict(c) for num, c in data.items()}
        print(f"✅ Données chargées depuis {fichier}")


# ============================================
# PARTIE 4 : Menu principal
# ============================================
def menu_principal():
    banque = Banque()
    banque.charger()
    
    while True:
        print("\n" + "="*50)
        print("🏦 SIMULATEUR DE COMPTE BANCAIRE")
        print("1. Créer un compte")
        print("2. Déposer")
        print("3. Retirer")
        print("4. Virement")
        print("5. Afficher solde")
        print("6. Historique")
        print("7. Lister comptes")
        print("8. Sauvegarder")
        print("9. Charger")
        print("0. Quitter")
        choix = input("Choix > ").strip()
         
        try:
            if choix == "1":
                numero = input("Numéro: ").strip()
                titulaire = input("Titulaire: ").strip()
                solde = float(input("Solde initial: ") or 0)
                banque.creer_compte(numero, titulaire, solde)
            elif choix == "2":
                num = input("Compte: ").strip()
                montant = float(input("Montant: "))
                if num in banque.comptes:
                    banque.comptes[num].deposer(montant)
                else:
                    print("❌ Compte introuvable")
            elif choix == "3":
                num = input("Compte: ").strip()
                montant = float(input("Montant: "))
                if num in banque.comptes:
                    banque.comptes[num].retirer(montant)
                else:
                    print("❌ Compte introuvable")
            elif choix == "4":
                src = input("Compte source: ").strip()
                dest = input("Compte destination: ").strip()
                montant = float(input("Montant: "))
                banque.virement(src, dest, montant)
            elif choix == "5":
                num = input("Compte: ").strip()
                if num in banque.comptes:
                    banque.comptes[num].afficher_solde()
            elif choix == "6":
                num = input("Compte: ").strip()
                if num in banque.comptes:
                    banque.comptes[num].afficher_historique()
            elif choix == "7":
                banque.lister_comptes()
            elif choix == "8":
                banque.sauvegarder()
            elif choix == "9":
                banque.charger()
            elif choix == "0":
                banque.sauvegarder()
                print("👋 Au revoir!")
                break
            else:
                print("❌ Choix invalide")
        except Exception as e:
            print(f"❌ Erreur: {e}")


# ============================================
# POINT D'ENTRÉE
# ============================================
if __name__ == "__main__":
    menu_principal()
