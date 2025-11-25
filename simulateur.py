import tkinter as tk
from tkinter import messagebox, simpledialog, ttk 
from datetime import datetime
import json
import os

class Operation:
    """Représente une opération bancaire avec date, type, montant et description"""
    def __init__(self, type_op, montant, description=""):
        self.date = datetime.now().isoformat()
        self.type = type_op
        self.montant = montant
        self.description = description
    
    def to_dict(self):
        return {"date": self.date, "type": self.type, "montant": self.montant, "description": self.description}
    
    @staticmethod
    def from_dict(data):
        op = Operation(data["type"], data["montant"], data.get("description", ""))
        op.date = data["date"]
        return op

class CompteBancaire:
    """Représente un compte bancaire avec solde, historique et limite de découvert"""
    def __init__(self, numero, titulaire, solde_initial=0, decouvert_max=0.0, is_loading=False):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde_initial
        self.decouvert_max = decouvert_max
        self.historique = []
        if solde_initial > 0 and not is_loading:
            self.historique.append(Operation("depot", solde_initial, "Solde initial"))
    
    def deposer(self, montant, description=""):
        if montant <= 0: return False
        self.solde += montant
        self.historique.append(Operation("depot", montant, description))
        return True
    
    def retirer(self, montant, description=""):
        if montant <= 0: return False
        seuil_decouvert = -self.decouvert_max
        nouveau_solde = self.solde - montant
        if nouveau_solde < seuil_decouvert: return False
        self.solde = nouveau_solde
        self.historique.append(Operation("retrait", montant, description))
        return True

    def to_dict(self):
        return {"numero": self.numero, "titulaire": self.titulaire, "solde": self.solde, "decouvert_max": self.decouvert_max, "historique": [op.to_dict() for op in self.historique]}
    
    @staticmethod
    def from_dict(data):
        decouvert = data.get("decouvert_max", 0.0)
        compte = CompteBancaire(data["numero"], data["titulaire"], data["solde"], decouvert, is_loading=True)
        compte.historique = [Operation.from_dict(op) for op in data["historique"]]
        return compte

class Banque:
    """Gère tous les comptes et opérations"""
    def __init__(self):
        self.comptes = {}
    
    def creer_compte(self, numero, titulaire, solde_initial=0, decouvert_max=0.0):
        if numero in self.comptes: return None
        compte = CompteBancaire(numero, titulaire, solde_initial, decouvert_max)
        self.comptes[numero] = compte
        return compte
    
    def supprimer_compte(self, numero):
        if numero in self.comptes:
            del self.comptes[numero]
            return True
        return False
    
    def virement(self, src, dest, montant):
        if src not in self.comptes or dest not in self.comptes or src == dest: return False
        
        # 1. Tente de retirer l'argent du compte source (Débit)
        if self.comptes[src].retirer(montant, description=f"Virement sortant vers {dest}"):
            
            # 2. Dépose l'argent sur le compte destination (Crédit) avec description pour le compte destination
            description_dest = f"Virement entrant de {src}"
            self.comptes[dest].deposer(montant, description=description_dest)
            
            return True
        return False

    def sauvegarder(self, fichier="banque.json"):
        data = {num: compte.to_dict() for num, compte in self.comptes.items()}
        try:
            with open(fichier, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Données sauvegardées dans {fichier}")
            return True
        except Exception as e:
            print(f"❌ Erreur de sauvegarde: {e}")
            return False
    
    def charger(self, fichier="banque.json"):
        if not os.path.exists(fichier):
            print("Fichier introuvable, banque vide")
            return
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.comptes = {num: CompteBancaire.from_dict(c) for num, c in data.items()}
            print(f"✅ Données chargées depuis {fichier}")
        except Exception as e:
             print(f"❌ Erreur de chargement: {e}")
             self.comptes = {}


class BanqueApp:
    def __init__(self, master):
        self.master = master
        master.title("🏦 Simulateur de Compte Bancaire (Fenêtre Unique)")
        master.geometry("700x750") 
        
        self.banque = Banque()
        self.banque.charger()
        
        self.compte_actuel_num = list(self.banque.comptes.keys())[0] if self.banque.comptes else None
        
        self.solde_var = tk.StringVar()
        self.titulaire_var = tk.StringVar()

        self.view_frame = tk.Frame(self.master)
        self.view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_widgets()
        self.show_main_view()

    # --- Méthodes de Gestion de la Vue ---

    def clear_view_frame(self):
        """Supprime tous les widgets du cadre de vue central."""
        for widget in self.view_frame.winfo_children():
            widget.destroy()

    def show_main_view(self):
        """Affiche la vue principale (Solde, Actions, Historique)."""
        self.clear_view_frame()
        
        # --- Cadre principal d'information du compte ---
        info_frame = tk.Frame(self.view_frame, padx=10, pady=10, bd=2, relief=tk.RIDGE)
        info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(info_frame, textvariable=self.titulaire_var, font=("Arial", 12)).pack(anchor=tk.W)
        tk.Label(info_frame, text="SOLDE ACTUEL :", font=("Arial", 16)).pack(pady=(10, 0))
        
        self.solde_label = tk.Label(info_frame, textvariable=self.solde_var, font=("Arial", 24, "bold"), fg="darkgreen")
        self.solde_label.pack(pady=(0, 10))

        # --- Cadre des opérations (Actions) ---
        action_frame = tk.Frame(self.view_frame, padx=10, pady=5)
        action_frame.pack(pady=5)
        
        tk.Button(action_frame, text="💰 Déposer", command=lambda: self.show_operation_view("depot"), width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(action_frame, text="💸 Retirer", command=lambda: self.show_operation_view("retrait"), width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(action_frame, text="🔄 Virement", command=lambda: self.show_operation_view("virement"), width=15).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Button(action_frame, text="📋 Liste/Changer de Compte", command=self.show_account_manager_view, width=22).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(action_frame, text="➕ Nouveau Compte", command=self.show_creation_dialog_view, width=18).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(action_frame, text="🗑️ Supprimer Compte", command=self.show_delete_account_view, width=18, bg="#dc3545", fg="white").grid(row=1, column=2, padx=5, pady=5)


        # --- Cadre de l'historique avec Treeview ---
        hist_frame = tk.LabelFrame(self.view_frame, text="Historique des Opérations", padx=10, pady=5)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("Date", "Type", "Montant", "Description")
        self.historique_tree = ttk.Treeview(hist_frame, columns=columns, show="headings")
        
        self.historique_tree.tag_configure('debit', foreground='red')
        self.historique_tree.tag_configure('credit', foreground='darkgreen')

        self.historique_tree.heading("Date", text="Date/Heure", anchor=tk.W)
        self.historique_tree.column("Date", width=150, anchor=tk.W)
        self.historique_tree.heading("Type", text="Type", anchor=tk.W)
        self.historique_tree.column("Type", width=80, anchor=tk.W)
        self.historique_tree.heading("Montant", text="Montant", anchor=tk.E)
        self.historique_tree.column("Montant", width=100, anchor=tk.E)
        self.historique_tree.heading("Description", text="Description", anchor=tk.W)
        # CORRECTION VISUELLE : Ajout de stretch=True pour s'assurer que la colonne prend l'espace restant
        self.historique_tree.column("Description", width=250, anchor=tk.W, stretch=True) 
        
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.historique_tree.yview)
        self.historique_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.historique_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.update_info_display() 


    def show_operation_view(self, operation_type):
        """Affiche la vue pour effectuer une opération (dépôt, retrait, virement)."""
        compte = self.get_compte_actuel()
        if not compte:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un compte actif avant d'effectuer une opération.")
            return

        self.clear_view_frame()
        
        titres = {
            "depot": "💰 Effectuer un Dépôt",
            "retrait": "💸 Effectuer un Retrait",
            "virement": "🔄 Effectuer un Virement",
        }

        operation_frame = tk.Frame(self.view_frame, padx=20, pady=20)
        operation_frame.pack(expand=True)
        
        tk.Label(operation_frame, text=titres.get(operation_type, "Opération"), font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(operation_frame, text=f"Compte Actif : {compte.numero} ({compte.titulaire})", font=("Arial", 12)).pack(pady=5)

        # --- Variables de contrôle ---
        montant_var = tk.DoubleVar()
        description_var = tk.StringVar()
        dest_num_var = tk.StringVar()
        
        form_frame = tk.Frame(operation_frame)
        form_frame.pack(padx=10, pady=10)
        
        # Champ Montant
        tk.Label(form_frame, text="Montant (€):", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        tk.Entry(form_frame, textvariable=montant_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        # Champ Description
        tk.Label(form_frame, text="Description:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        tk.Entry(form_frame, textvariable=description_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        # Champ Compte Destination (uniquement pour Virement)
        if operation_type == "virement":
            tk.Label(form_frame, text="N° Compte Destination:", anchor='w').grid(row=2, column=0, sticky='w', pady=5)
            compte_options = [num for num in self.banque.comptes.keys() if num != compte.numero]
            dest_combo = ttk.Combobox(form_frame, textvariable=dest_num_var, values=compte_options, state="readonly", width=28)
            dest_combo.grid(row=2, column=1, padx=5, pady=5)


        # --- Fonction de validation et d'exécution ---
        def execute_operation():
            try:
                montant = montant_var.get()
                description = description_var.get()
            except tk.TclError:
                messagebox.showerror("Erreur", "Veuillez entrer un montant numérique valide.")
                return

            if montant <= 0:
                messagebox.showerror("Erreur", "Le montant doit être strictement positif.")
                return
                
            success = False

            if operation_type == "depot":
                success = compte.deposer(montant, description)
                messagebox.showinfo("Succès", f"Dépôt de {montant:.2f}€ réussi.")
            
            elif operation_type == "retrait":
                success = compte.retirer(montant, description)
                if not success:
                    msg = f"Retrait impossible. Solde insuffisant : dépasserait la limite de découvert (-{compte.decouvert_max:.2f}€)." if compte.decouvert_max > 0 else "Retrait impossible. Solde insuffisant (découvert non autorisé)."
                    messagebox.showerror("Erreur", msg)
                    return
                messagebox.showinfo("Succès", f"Retrait de {montant:.2f}€ réussi.")

            elif operation_type == "virement":
                dest_num = dest_num_var.get()
                if not dest_num or dest_num == compte.numero:
                    messagebox.showerror("Erreur", "Veuillez sélectionner un compte destination différent.")
                    return
                if dest_num not in self.banque.comptes:
                    messagebox.showerror("Erreur", "Compte destination introuvable.")
                    return
                
                # La description est gérée dans la méthode banque.virement
                success = self.banque.virement(compte.numero, dest_num, montant)
                
                if not success:
                    msg = f"Virement impossible. Solde insuffisant : dépasserait la limite de découvert (-{compte.decouvert_max:.2f}€)." if compte.decouvert_max > 0 else "Virement impossible. Solde insuffisant (découvert non autorisé)."
                    messagebox.showerror("Erreur", msg)
                    return
                messagebox.showinfo("Succès", f"Virement de {montant:.2f}€ vers {dest_num} réussi.")

            if success:
                self.show_main_view() # Retour à la vue principale


        # --- Boutons d'action ---
        button_frame = tk.Frame(operation_frame)
        button_frame.pack(pady=20)

        action_text = "Déposer" if operation_type == "depot" else ("Retirer" if operation_type == "retrait" else "Effectuer Virement")
        
        tk.Button(button_frame, text=action_text, command=execute_operation, bg="#007bff", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Annuler/Retour", command=self.show_main_view).pack(side=tk.LEFT, padx=10)


    def show_creation_dialog_view(self):
        """Affiche la vue de création de compte."""
        self.clear_view_frame()
        
        dialog_frame = tk.Frame(self.view_frame, padx=20, pady=20)
        dialog_frame.pack(expand=True)
        
        tk.Label(dialog_frame, text="➕ Créer un Nouveau Compte", font=("Arial", 16, "bold")).pack(pady=10)

        num_var = tk.StringVar()
        titulaire_var = tk.StringVar()
        decouvert_var = tk.DoubleVar(value=0.0)
        solde_var = tk.DoubleVar(value=0.0)

        main_form_frame = tk.Frame(dialog_frame, padx=15, pady=15)
        main_form_frame.pack(padx=10, pady=10)

        def valider_creation():
            numero = num_var.get()
            titulaire = titulaire_var.get()
            
            if not numero or not titulaire:
                messagebox.showerror("Erreur", "Le numéro et le titulaire sont obligatoires.")
                return

            try:
                decouvert = decouvert_var.get()
                solde = solde_var.get()
            except tk.TclError:
                messagebox.showerror("Erreur", "Veuillez entrer des nombres valides.")
                return

            if decouvert < 0:
                 messagebox.showerror("Erreur", "Le découvert doit être positif ou nul.")
                 return
            if solde < 0:
                messagebox.showerror("Erreur", "Le solde initial ne peut pas être négatif.")
                return

            if self.banque.creer_compte(numero, titulaire, solde, decouvert):
                self.set_compte_actuel(numero) 
                messagebox.showinfo("Succès", f"Compte {numero} créé pour {titulaire} (Découvert max: {decouvert:.2f}€).")
                self.show_main_view()
            else:
                messagebox.showerror("Erreur", "La création du compte a échoué (ce numéro existe déjà).")

        # --- Création des champs ---
        tk.Label(main_form_frame, text="Numéro de Compte:", anchor='w').grid(row=0, column=0, sticky='w', pady=2)
        tk.Entry(main_form_frame, textvariable=num_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        tk.Label(main_form_frame, text="Titulaire:", anchor='w').grid(row=1, column=0, sticky='w', pady=2)
        tk.Entry(main_form_frame, textvariable=titulaire_var, width=30).grid(row=1, column=1, padx=5, pady=2)
        tk.Label(main_form_frame, text="Solde Initial (€):", anchor='w').grid(row=2, column=0, sticky='w', pady=2)
        tk.Entry(main_form_frame, textvariable=solde_var, width=30).grid(row=2, column=1, padx=5, pady=2)
        tk.Label(main_form_frame, text="Découvert Max (€):", anchor='w').grid(row=3, column=0, sticky='w', pady=2)
        tk.Entry(main_form_frame, textvariable=decouvert_var, width=30).grid(row=3, column=1, padx=5, pady=2)


        # --- Boutons ---
        button_frame = tk.Frame(dialog_frame)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Créer le Compte", command=valider_creation, bg="#28a745", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Retour à l'Accueil", command=self.show_main_view).pack(side=tk.LEFT, padx=10)


    def show_account_manager_view(self):
        """Affiche la vue de gestion des comptes (liste et changement de compte)."""
        self.clear_view_frame()
        
        if not self.banque.comptes:
            messagebox.showinfo("Information", "Aucun compte n'existe encore. Créez-en un.")
            self.show_main_view()
            return

        manager_frame = tk.Frame(self.view_frame, padx=10, pady=10)
        manager_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(manager_frame, text="📋 Liste et Gestion des Comptes", font=("Arial", 16, "bold")).pack(pady=10)

        columns = ("Numero", "Titulaire", "Solde", "Découvert", "Dernière Opération")
        compte_list_tree = ttk.Treeview(manager_frame, columns=columns, show="headings")
        
        compte_list_tree.heading("Numero", text="N° Compte", anchor=tk.W)
        compte_list_tree.heading("Titulaire", text="Titulaire", anchor=tk.W)
        compte_list_tree.heading("Solde", text="Solde", anchor=tk.E)
        compte_list_tree.heading("Découvert", text="Découvert Max", anchor=tk.E)
        compte_list_tree.heading("Dernière Opération", text="Dernière Opération", anchor=tk.W)
        
        compte_list_tree.column("Numero", width=90)
        compte_list_tree.column("Titulaire", width=120)
        compte_list_tree.column("Solde", anchor=tk.E, width=90)
        compte_list_tree.column("Découvert", anchor=tk.E, width=110)
        compte_list_tree.column("Dernière Opération", anchor=tk.W, width=170) 
        
        compte_list_tree.tag_configure('negatif', foreground='red')

        for num, compte in self.banque.comptes.items():
            solde_str = f"{compte.solde:.2f} €"
            decouvert_str = f"{compte.decouvert_max:.2f} €"
            tag = 'negatif' if compte.solde < 0 else ''
            
            if compte.historique:
                derniere_op_iso = compte.historique[-1].date 
                derniere_op_str = datetime.fromisoformat(derniere_op_iso).strftime('%Y-%m-%d %H:%M:%S')
            else:
                derniere_op_str = "Aucune"

            compte_list_tree.insert("", tk.END, 
                                    values=(num, compte.titulaire, solde_str, decouvert_str, derniere_op_str), 
                                    tags=(tag, num)) 

        compte_list_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # --- Fonction de changement de compte (intégrée) ---
        def select_compte_and_close():
            selection = compte_list_tree.selection()
            if selection:
                item_id = selection[0]
                # CORRECTION : Utilisation de 'values' pour récupérer le numéro de compte sélectionné.
                numero_choisi = compte_list_tree.item(item_id, 'values')[0] 
                
                if self.set_compte_actuel(numero_choisi):
                    messagebox.showinfo("Succès", f"Compte {numero_choisi} sélectionné comme compte actif.")
                self.show_main_view()
            else:
                messagebox.showwarning("Sélection", "Veuillez sélectionner un compte pour le définir comme actif.")
        
        button_frame = tk.Frame(manager_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Définir comme Compte Actif", command=select_compte_and_close).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Retour à l'Accueil", command=self.show_main_view).pack(side=tk.LEFT, padx=10)


    def show_delete_account_view(self):
        """Affiche la vue dédiée à la suppression d'un compte."""
        self.clear_view_frame()
        
        if not self.banque.comptes:
            messagebox.showinfo("Info", "Aucun compte à supprimer.")
            self.show_main_view()
            return
            
        delete_frame = tk.Frame(self.view_frame, padx=20, pady=20)
        delete_frame.pack(expand=True)
        
        tk.Label(delete_frame, text="🗑️ Supprimer un Compte", font=("Arial", 16, "bold"), fg="red").pack(pady=10)
        tk.Label(delete_frame, text="Attention: Cette action est irréversible.", fg="red").pack(pady=5)

        # --- Variables de contrôle ---
        compte_a_supprimer_var = tk.StringVar()
        compte_options = list(self.banque.comptes.keys())
        
        # Champ de sélection du compte
        form_frame = tk.Frame(delete_frame, padx=15, pady=15)
        form_frame.pack(padx=10, pady=10)
        
        tk.Label(form_frame, text="Sélectionnez le compte à supprimer:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        
        compte_combo = ttk.Combobox(form_frame, textvariable=compte_a_supprimer_var, values=compte_options, state="readonly", width=30)
        compte_combo.grid(row=0, column=1, padx=5, pady=5)
        if compte_options:
            compte_combo.set(self.compte_actuel_num if self.compte_actuel_num in compte_options else compte_options[0])

        # --- Fonction d'exécution de la suppression ---
        def execute_delete():
            compte_num_to_delete = compte_a_supprimer_var.get()
            
            if not compte_num_to_delete or compte_num_to_delete not in self.banque.comptes:
                messagebox.showerror("Erreur", "Veuillez sélectionner un compte valide.")
                return
            
            confirm = messagebox.askyesno("Confirmation", 
                                          f"Êtes-vous SÛR de vouloir supprimer le compte {compte_num_to_delete} ?\nCette action est irréversible.", 
                                          parent=delete_frame) 
                                          
            if confirm:
                if self.banque.supprimer_compte(compte_num_to_delete):
                    messagebox.showinfo("Succès", f"Le compte {compte_num_to_delete} a été supprimé.")
                    
                    if compte_num_to_delete == self.compte_actuel_num:
                        self.compte_actuel_num = list(self.banque.comptes.keys())[0] if self.banque.comptes else None
                            
                    self.show_main_view() # Retour à l'accueil
                else:
                    messagebox.showerror("Erreur", "La suppression du compte a échoué (erreur interne).")


        # --- Boutons ---
        button_frame = tk.Frame(delete_frame)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="CONFIRMER SUPPRESSION", command=execute_delete, bg="red", fg="white", width=25).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Annuler/Retour", command=self.show_main_view).pack(side=tk.LEFT, padx=10)


    # --- Méthodes Utilitaires ---

    def create_widgets(self):
        tk.Button(self.master, text="💾 Sauvegarder & Quitter", command=self.on_closing, bg="#007bff", fg="white").pack(fill=tk.X, padx=10, pady=10)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_compte_actuel(self):
        return self.banque.comptes.get(self.compte_actuel_num)
    
    def set_compte_actuel(self, numero):
        if numero in self.banque.comptes:
            self.compte_actuel_num = numero
            self.update_info_display()
            return True
        return False

    def update_info_display(self):
        compte = self.get_compte_actuel()
        if compte:
            self.titulaire_var.set(f"Compte : {compte.numero} ({compte.titulaire}) - Découvert max: {compte.decouvert_max:.2f}€")
            self.solde_var.set(f"{compte.solde:.2f} €")
            if compte.solde < 0:
                self.solde_label.config(fg="red")
            else:
                self.solde_label.config(fg="darkgreen")
            self.update_historique_list()
        else:
            self.titulaire_var.set("Aucun compte sélectionné. Veuillez créer un compte.")
            self.solde_var.set("0.00 €")
            self.solde_label.config(fg="black")
            if hasattr(self, 'historique_tree'):
                self.historique_tree.delete(*self.historique_tree.get_children())


    def update_historique_list(self):
        """Met à jour le Treeview de l'historique, y compris la description."""
        if not hasattr(self, 'historique_tree'): return 
        
        compte = self.get_compte_actuel()
        self.historique_tree.delete(*self.historique_tree.get_children()) 
        
        if compte:
            for op in reversed(compte.historique): 
                date_str = datetime.fromisoformat(op.date).strftime('%Y-%m-%d %H:%M:%S')
                montant_str = f"{op.montant:,.2f} €".replace(",", " ")
                tag = "debit" if op.type in ["retrait", "virement_out"] else "credit"
                
                # Description correctement incluse
                self.historique_tree.insert("", tk.END, 
                                            values=(date_str, op.type.upper(), montant_str, op.description), 
                                            tags=(tag,))
                
    def on_closing(self):
        self.banque.sauvegarder()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BanqueApp(root)
    root.mainloop()