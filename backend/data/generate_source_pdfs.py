"""
Génère les PDFs sources utilisés par le pipeline d'ingestion (data/pdfs/).

Contexte : il n'existe pas, à ce jour, un PDF officiel unique et téléchargeable
qui couvre chaque démarche (CNIB, passeport, création d'entreprise) de façon
complète. Le portail service-public.gov.bf présente cette information sous
forme de fiches HTML, parfois incomplètes après sa refonte (v2.0, mai 2026).

Ce script compile donc le contenu officiel (vérifié manuellement sur les sites
ci-dessous le 29/06/2026) en 3 PDFs, un par démarche, avec la source précisée
en pied de page de chaque fiche. C'est ce contenu, et uniquement celui-ci, que
le pipeline d'ingestion (extract_pdf.py) va lire et indexer.

Sources officielles utilisées :
- https://police.gov.bf/index.php/infos-utiles/cnib
- https://service-public.gov.bf/thematiques/etat-civil-identite-famille/demande-detablissement-ou-de-renouvellement-de-la-cnib
- https://police.gov.bf/index.php/infos-utiles/passeport
- https://service-public.gov.bf/thematiques/creation-dentreprise/creation-dentreprise-demande-de-creation-dentreprises-pour-les-personnes-physiques
- https://service-public.gov.bf/thematiques/creation-dentreprise/creation-dentreprise-demande-de-creation-dentreprises-pour-les-personnes-morales

Usage :
    python data/generate_source_pdfs.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem,
)

OUT_DIR = os.path.join(os.path.dirname(__file__), "pdfs")
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitreDoc", parent=styles["Title"], fontSize=18, spaceAfter=14)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6)
body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5, leading=15, alignment=TA_LEFT)
meta = ParagraphStyle("Meta", parent=styles["BodyText"], fontSize=9, textColor="#555555", leading=13)
source = ParagraphStyle("Source", parent=styles["BodyText"], fontSize=8.5, textColor="#777777", leading=12, spaceBefore=4)


def build_pdf(filename, title, blocks):
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    story = [Paragraph(title, title_style), Spacer(1, 6)]

    for block in blocks:
        kind = block[0]
        if kind == "h2":
            story.append(Paragraph(block[1], h2))
        elif kind == "p":
            story.append(Paragraph(block[1], body))
        elif kind == "meta":
            story.append(Paragraph(block[1], meta))
        elif kind == "list":
            items = [ListItem(Paragraph(t, body), leftIndent=10) for t in block[1]]
            story.append(ListFlowable(items, bulletType="bullet", start="•"))
        elif kind == "source":
            story.append(Paragraph(f"Source officielle : {block[1]}", source))
        elif kind == "space":
            story.append(Spacer(1, block[1]))

    doc.build(story)
    print(f"OK -> {path}")


# ---------------------------------------------------------------------------
# 1. CNIB
# ---------------------------------------------------------------------------
build_pdf(
    "cnib.pdf",
    "Carte Nationale d'Identité Burkinabè (CNIB)",
    [
        ("meta", "Démarche : cnib | Mis à jour le 26/06/2026"),
        ("h2", "Description"),
        ("p", "La Carte Nationale d'Identité Burkinabè (CNIB) est un document officiel qui "
              "permet à tout citoyen de justifier son identité et sa nationalité burkinabè. "
              "Elle est obligatoire à partir de l'âge de 15 ans révolus et a une durée de "
              "validité de 10 ans. C'est une carte biométrique sécurisée (empreintes "
              "digitales et, depuis 2009, biométrie faciale), difficilement falsifiable."),
        ("h2", "Qui peut faire cette démarche ?"),
        ("list", [
            "Être âgé de 15 ans révolus ou plus.",
            "Être de nationalité burkinabè.",
        ]),
        ("h2", "Pièces à fournir pour une première demande"),
        ("p", "<b>Pour les Burkinabè nés au Burkina Faso :</b>"),
        ("list", [
            "Une copie de l'acte de naissance (ou jugement supplétif d'acte de naissance).",
        ]),
        ("p", "<b>Pour les Burkinabè nés à l'extérieur du Burkina Faso :</b>"),
        ("list", [
            "Une copie du certificat de nationalité.",
            "Un formulaire de demande de carte nationale d'identité (remis sur place) à compléter.",
        ]),
        ("p", "Pièces complémentaires selon le cas : une copie légalisée de l'acte de mariage "
              "pour les femmes désirant porter le nom de leur époux ; une copie du registre "
              "du commerce pour faire figurer la profession de commerçant sur la carte ; "
              "des timbres fiscaux de 2 500 F CFA."),
        ("h2", "Coût et délai"),
        ("list", [
            "Coût : 2 500 F CFA (timbres fiscaux).",
            "Délai : variable selon la localité, en général entre 7 et 30 jours "
            "(2 à 3 semaines en moyenne), selon la distance entre le Centre de Traitement "
            "Intermédiaire des Données (CTID) et le centre de production de l'ONI.",
        ]),
        ("h2", "Où faire la demande"),
        ("p", "Le demandeur doit se présenter en personne dans un Centre de Collecte des "
              "Données (CCD), généralement installé dans les commissariats de police ou "
              "certaines mairies. Le retrait se fait au même CCD, sur présentation du "
              "récépissé remis lors du dépôt. En cas de déménagement, un changement de "
              "lieu de retrait peut être demandé directement auprès de la direction "
              "générale de l'ONI."),
        ("h2", "Perte ou vol de la CNIB"),
        ("p", "En cas de perte, il convient de faire une déclaration de perte dans un "
              "commissariat de police avant de pouvoir déposer une nouvelle demande de CNIB."),
        ("space", 10),
        ("source", "https://police.gov.bf/index.php/infos-utiles/cnib"),
        ("source", "https://service-public.gov.bf/thematiques/etat-civil-identite-famille/"
                    "demande-detablissement-ou-de-renouvellement-de-la-cnib"),
    ],
)

# ---------------------------------------------------------------------------
# 2. Passeport ordinaire
# ---------------------------------------------------------------------------
build_pdf(
    "passeport.pdf",
    "Passeport ordinaire",
    [
        ("meta", "Démarche : passeport | Mis à jour le 07/06/2026"),
        ("h2", "Description"),
        ("p", "Le passeport ordinaire est délivré par la Direction Générale de la Police "
              "Nationale, à travers la Division de la Migration (sise à Gounghin, "
              "Ouagadougou). Depuis le 30 août 2018, le Burkina Faso délivre un passeport "
              "biométrique (e-passeport), conforme aux normes de l'Organisation de "
              "l'Aviation Civile Internationale (OACI). Le dossier se dépose tous les "
              "matins, du lundi au vendredi."),
        ("h2", "Pièces à fournir - pour les majeurs"),
        ("list", [
            "Une copie légalisée de l'acte de naissance.",
            "Une copie légalisée du certificat de nationalité burkinabè.",
            "Une copie légalisée de la CNIB.",
            "Un extrait de casier judiciaire en cours de validité.",
            "Un timbre fiscal de 200 F CFA.",
            "Trois (3) photos d'identité au format passeport.",
            "Un document justifiant la profession du demandeur.",
            "La somme de cinquante mille (50 000) F CFA pour les frais d'établissement.",
        ]),
        ("p", "Pour les femmes mariées souhaitant porter le nom de leur conjoint sur le "
              "passeport : joindre en plus une copie légalisée de l'acte de mariage."),
        ("h2", "Pièces à fournir - pour les mineurs"),
        ("list", [
            "L'acte de naissance de l'enfant.",
            "Le certificat de nationalité de l'enfant.",
            "Une autorisation parentale.",
            "Le document d'identité des deux parents (ou, si les parents résident hors du "
            "Burkina Faso, leur titre de séjour ; dans ce cas l'autorisation parentale "
            "n'est plus nécessaire).",
            "Un timbre fiscal de 200 F CFA, plus la somme de 50 000 F CFA.",
            "Trois (3) photos au format passeport.",
        ]),
        ("p", "Pour les militaires et paramilitaires : joindre un certificat de présence "
              "au corps précisant l'établissement d'un passeport."),
        ("h2", "Coût et délai"),
        ("list", [
            "Coût : 50 000 F CFA + un timbre fiscal de 200 F CFA.",
            "Délai : 72 heures ouvrables si le dossier est complet et régulier "
            "(peut varier en cas de rupture de stock de carnets passeport).",
        ]),
        ("p", "<i>Recommandation officielle : éviter de passer par des intermédiaires.</i>"),
        ("space", 10),
        ("source", "https://police.gov.bf/index.php/infos-utiles/passeport"),
        ("source", "https://service-public.gov.bf/thematiques/etat-civil-identite-famille/"
                    "demande-de-passeport-ordinaire"),
    ],
)

# ---------------------------------------------------------------------------
# 3. Création d'entreprise
# ---------------------------------------------------------------------------
build_pdf(
    "creation_entreprise.pdf",
    "Création d'entreprise (CEFORE)",
    [
        ("meta", "Démarche : creation_entreprise | Mis à jour le 29/06/2026"),
        ("h2", "Description générale"),
        ("p", "Le Centre de Formalités des Entreprises (CEFORE), installé à la Maison de "
              "l'Entreprise du Burkina Faso (MEBF), est le guichet unique chargé "
              "d'accomplir les formalités de création d'entreprise. Les modalités diffèrent "
              "selon que le promoteur crée une entreprise en tant que personne physique "
              "(entreprise individuelle) ou personne morale (société)."),
        ("h2", "Création pour une personne physique (entreprise individuelle)"),
        ("p", "La création pour une personne physique regroupe quatre formalités :"),
        ("list", [
            "Le Registre du Commerce et du Crédit Mobilier (RCCM).",
            "La déclaration d'existence fiscale et l'Identifiant Financier Unique (IFU).",
            "La Carte Professionnelle de Commerçant (CPC).",
            "La notification employeur auprès de la Caisse Nationale de Sécurité Sociale (CNSS).",
        ]),
        ("p", "Qui peut faire cette démarche : toute personne juridiquement capable "
              "d'exercer le commerce."),
        ("list", [
            "Coût : 40 000 F CFA.",
            "Délai : environ 3 mois.",
        ]),
        ("h2", "Création pour une personne morale (société)"),
        ("p", "La création pour une personne morale regroupe trois formalités :"),
        ("list", [
            "Le Registre du Commerce et du Crédit Mobilier (RCCM).",
            "La déclaration d'existence fiscale et l'Identifiant Financier Unique (IFU).",
            "La notification employeur auprès de la CNSS.",
        ]),
        ("p", "Qui peut faire cette démarche : toute personne juridiquement capable "
              "d'exercer le commerce."),
        ("list", [
            "Coût : 47 500 F CFA.",
            "Délai : environ 3 mois.",
        ]),
        ("h2", "Pièces à fournir et où déposer le dossier"),
        ("p", "Selon le portail officiel, aucune pièce justificative n'est exigée en amont "
              "pour initier la procédure ; le dossier (formulaires CEFORE, pièce d'identité "
              "du promoteur, statuts pour les sociétés) se constitue directement au guichet "
              "CEFORE de la Maison de l'Entreprise du Burkina Faso, qui centralise les "
              "démarches RCCM, IFU, CPC et CNSS."),
        ("space", 10),
        ("source", "https://service-public.gov.bf/thematiques/creation-dentreprise/"
                    "creation-dentreprise-demande-de-creation-dentreprises-pour-les-personnes-physiques"),
        ("source", "https://service-public.gov.bf/thematiques/creation-dentreprise/"
                    "creation-dentreprise-demande-de-creation-dentreprises-pour-les-personnes-morales"),
    ],
)

# ---------------------------------------------------------------------------
# 4. Casier judiciaire (bulletin n°3)
# ---------------------------------------------------------------------------
build_pdf(
    "casier_judiciaire.pdf",
    "Extrait de Casier Judiciaire (Bulletin n°3)",
    [
        ("meta", "Démarche : casier_judiciaire | Mis à jour le 29/06/2026"),
        ("h2", "Description"),
        ("p", "L'extrait de casier judiciaire (bulletin n°3) est un document délivré par "
              "le Ministère de la Justice attestant qu'une personne n'a pas (ou a) fait "
              "l'objet de certaines condamnations. Il est notamment exigé pour la demande "
              "de passeport, certains concours et recrutements. Depuis 2023, le Ministère "
              "de la Justice propose la plateforme en ligne e-CasierJudiciaire, qui permet "
              "d'obtenir ce document sans se déplacer."),
        ("h2", "Qui peut faire cette démarche ?"),
        ("p", "Tout public. <b>Important :</b> la demande en ligne via e-CasierJudiciaire "
              "n'est pour l'instant ouverte qu'aux personnes nées dans les provinces du "
              "Kadiogo, du Ganzourgou et du Bazèga, car seuls les Tribunaux de Grande "
              "Instance (TGI) de Ouaga I et Ouaga II sont habilités à délivrer le e-casier. "
              "Les personnes nées dans une autre province doivent effectuer la demande de "
              "façon classique auprès du Tribunal de Grande Instance compétent pour leur "
              "lieu de naissance."),
        ("h2", "Pièces à fournir"),
        ("list", [
            "Un extrait d'acte de naissance (ou jugement supplétif d'acte de naissance).",
            "Une copie de la CNIB ou du passeport.",
        ]),
        ("h2", "Procédure en ligne (e-CasierJudiciaire)"),
        ("list", [
            "Se rendre sur le site www.ecasier-judiciaire.gov.bf.",
            "Cliquer sur « Faire sa demande » et renseigner les informations demandées.",
            "Téléverser les pièces demandées (CNIB et extrait d'acte de naissance).",
            "Relire le récapitulatif des informations fournies et valider la demande.",
            "Cliquer sur « Effectuer le paiement » et choisir le moyen de paiement mobile money.",
            "Suivre la procédure de paiement indiquée (ex. avec Orange Money : composer "
            "*144*4*6*750# pour générer un code OTP, puis le saisir pour valider le paiement).",
            "Télécharger le récépissé de demande, puis recevoir le document par voie électronique.",
        ]),
        ("h2", "Coût et délai"),
        ("list", [
            "Coût : 750 F CFA, payable par mobile money (Orange Money, Moov Money, "
            "Coris Money, Liguidicash ou Ginfray).",
            "Délai : variable selon le portail officiel service-public.gov.bf.",
        ]),
        ("h2", "Où faire la demande (procédure classique)"),
        ("p", "Pour les personnes nées hors des provinces du Kadiogo, du Ganzourgou et du "
              "Bazèga, la demande se fait directement auprès du Tribunal de Grande Instance "
              "(TGI) du lieu de naissance du demandeur, sur présentation des mêmes pièces "
              "(acte de naissance et pièce d'identité)."),
        ("space", 10),
        ("source", "https://ecasier-judiciaire.gov.bf/"),
        ("source", "https://service-public.gov.bf/thematiques/etat-civil-identite-famille/"
                    "demande-de-casier-judiciaire"),
        ("source", "https://www.service-public.gov.bf/actualites/"
                    "e-casierjudiciaire-demandez-votre-casier-en-ligne"),
        ("source", "https://www.orange.bf/fr/assistance/e-casier-judiciaire.html"),
    ],
)

# --------------------------------------------