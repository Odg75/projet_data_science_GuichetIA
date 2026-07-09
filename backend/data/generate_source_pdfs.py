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
- https://oni.bf/nos-prestations/cnib/
- https://oni.bf/nos-prestations/passeport/
- https://police.gov.bf/index.php/infos-utiles/cnib
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
        ("meta", "Démarche : cnib | Mis à jour le 07/07/2026 — Source : oni.bf"),
        ("h2", "Description"),
        ("p", "La Carte Nationale d'Identité Burkinabè (CNIB) est un document officiel qui "
              "permet à tout citoyen de justifier son identité et sa nationalité burkinabè. "
              "Elle est obligatoire à partir de l'âge de 15 ans révolus et a une durée de "
              "validité de 10 ans. C'est une carte biométrique sécurisée délivrée par "
              "l'Office National d'Identification (ONI)."),
        ("h2", "Pièces à fournir pour une première demande"),
        ("p", "<b>Pour les Burkinabè nés au Burkina Faso :</b>"),
        ("list", [
            "Un extrait d'acte de naissance.",
            "Un formulaire de demande de carte nationale d'identité (fourni par l'administration) à compléter.",
        ]),
        ("p", "<b>Pour les Burkinabè nés hors du Burkina Faso :</b>"),
        ("list", [
            "Un certificat de nationalité.",
            "Un formulaire de demande de carte nationale d'identité (fourni par l'administration) à compléter.",
        ]),
        ("p", "Pièces complémentaires selon le cas :"),
        ("list", [
            "Pour les femmes désirant porter le nom de leur époux : une copie de l'acte de mariage.",
            "Pour certaines professions (commerçant, médecin, magistrat, etc.) : un document justificatif.",
        ]),
        ("h2", "Coût et validité"),
        ("list", [
            "Coût : 2 500 F CFA.",
            "Durée de validité : dix (10) ans.",
        ]),
        ("h2", "Conditions de renouvellement"),
        ("p", "Les différents motifs de renouvellement de la CNIB :"),
        ("list", [
            "Expiration de la validité de la CNIB.",
            "Perte (la demande doit être accompagnée d'une déclaration de perte faite dans un commissariat de police).",
            "Altération (la demande doit être accompagnée de la carte altérée).",
            "Vol de la CNIB (la demande doit être accompagnée d'une déclaration de perte).",
            "Demande de changement d'adresse habituelle.",
            "Demande de modification du prénom, du nom, de la date de naissance, ou rectification du lieu de naissance.",
        ]),
        ("h2", "Où faire la demande"),
        ("p", "Le demandeur doit se présenter en personne dans un Centre de Collecte des "
              "Données (CCD), généralement installé dans les commissariats de police ou "
              "certaines mairies. Le retrait se fait au même CCD, sur présentation du "
              "récépissé remis lors du dépôt."),
        ("space", 10),
        ("source", "https://oni.bf/nos-prestations/cnib/"),
        ("source", "https://www.police.gov.bf/index.php/infos-utiles/cnib"),
    ],
)

# ---------------------------------------------------------------------------
# 2. Passeport ordinaire
# ---------------------------------------------------------------------------
build_pdf(
    "passeport.pdf",
    "Passeport ordinaire",
    [
        ("meta", "Démarche : passeport | Mis à jour le 07/07/2026 — Source : oni.bf"),
        ("h2", "Description"),
        ("p", "Le passeport ordinaire est délivré par l'Office National d'Identification (ONI), "
              "à travers la Division de la Migration. Depuis le 30 août 2018, le Burkina Faso "
              "délivre un passeport biométrique (e-passeport), conforme aux normes de "
              "l'Organisation de l'Aviation Civile Internationale (OACI)."),
        ("h2", "Coût et validité"),
        ("list", [
            "Coût : 50 000 F CFA.",
            "Durée de validité : cinq (05) ans.",
        ]),
        ("h2", "Délai d'établissement"),
        ("p", "La durée d'établissement est de <b>soixante-douze (72) heures ouvrables</b> "
              "si le dossier est complet et régulier. En cas d'insuffisance de stocks de "
              "passeports, le délai peut varier en fonction de l'urgence. "
              "<b>Recommandation officielle : éviter de passer par des intermédiaires.</b>"),
        ("h2", "Pièces à fournir — pour les majeurs"),
        ("p", "Composition du dossier d'une demande de passeport (à déposer à la Division "
              "de la Migration tous les matins du lundi au vendredi) :"),
        ("list", [
            "Une copie légalisée de l'acte de naissance.",
            "Une copie légalisée du certificat de nationalité burkinabè.",
            "Une copie légalisée de la Carte Nationale d'Identité Burkinabè (CNIB).",
            "Un casier judiciaire en cours de validité.",
            "Un timbre fiscal de 200 F CFA.",
            "Trois (03) photos d'identité au format passeport.",
            "Un document justifiant la profession.",
            "La somme de 50 000 F CFA pour les frais d'établissement.",
        ]),
        ("p", "<b>Pour les femmes mariées souhaitant porter le nom de l'époux :</b> "
              "joindre en plus une copie légalisée de l'acte de mariage aux pièces "
              "listées ci-dessus."),
        ("p", "<b>Pour les militaires et paramilitaires :</b> "
              "joindre un certificat de présence au corps précisant l'établissement "
              "d'un passeport."),
        ("h2", "Pièces à fournir — pour les mineurs"),
        ("list", [
            "L'acte de naissance de l'enfant.",
            "Le certificat de nationalité de l'enfant.",
            "Une autorisation parentale (non requise si les parents résident à l'étranger).",
            "Document d'identité des deux parents si le mineur réside au Burkina Faso ; "
            "titre de séjour des deux parents si les parents résident à l'étranger.",
            "Un timbre fiscal de 200 F CFA.",
            "La somme de 50 000 F CFA pour les frais d'établissement.",
            "Trois (03) photos d'identité au format passeport.",
        ]),
        ("h2", "Conditions de renouvellement"),
        ("p", "Un passeport peut être renouvelé pour les motifs suivants :"),
        ("list", [
            "Expiration de la validité.",
            "Validité insuffisante pour le voyage envisagé.",
            "Perte (la demande doit être accompagnée d'une déclaration faite auprès de la Division de la Migration).",
            "Détérioration du passeport.",
            "Vol.",
            "Pages saturées.",
            "Ajout du nom du conjoint.",
            "Modification du prénom, du nom ou de la date de naissance.",
        ]),
        ("h2", "Où faire la demande"),
        ("p", "Le dossier se dépose à la Division de la Migration (sise à Gounghin, Ouagadougou), "
              "tous les matins du lundi au vendredi. "
              "<i>Recommandation officielle : éviter de passer par des intermédiaires.</i>"),
        ("space", 10),
        ("source", "https://oni.bf/nos-prestations/passeport/"),
        ("source", "https://www.police.gov.bf/index.php/infos-utiles/passeport"),
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

# ---------------------------------------------------------------------------
# 5. Acte de naissance
# ---------------------------------------------------------------------------
build_pdf(
    "acte_naissance.pdf",
    "Acte de naissance (Burkina Faso)",
    [
        ("meta", "Démarche : acte_naissance | Mis à jour le 06/07/2026"),
        ("h2", "Description"),
        ("p", "L'acte de naissance est un document officiel d'état civil attestant "
              "la naissance d'une personne. Il est délivré par les centres d'état civil "
              "(mairies ou communes) et est indispensable pour toute démarche administrative : "
              "CNIB, passeport, scolarité, mariage, etc."),
        ("h2", "Déclaration de naissance"),
        ("p", "La déclaration de naissance doit être effectuée dans les 30 jours suivant "
              "la naissance auprès du centre d'état civil du lieu de naissance. Passé ce délai, "
              "la déclaration tardive nécessite un jugement supplétif d'acte de naissance "
              "délivré par le Tribunal de Grande Instance (TGI)."),
        ("h2", "Pièces à fournir pour une déclaration de naissance"),
        ("list", [
            "Le certificat médical de naissance ou une attestation de l'accoucheuse.",
            "La pièce d'identité du déclarant (père, mère ou représentant légal).",
            "Le livret de famille des parents (si disponible).",
        ]),
        ("h2", "Pièces à fournir pour obtenir une copie d'acte de naissance"),
        ("list", [
            "Les informations sur la personne concernée (nom, prénom, date et lieu de naissance).",
            "La pièce d'identité du demandeur (CNIB ou passeport).",
            "Le livret de famille (si disponible, pour faciliter la recherche).",
        ]),
        ("h2", "Jugement supplétif d'acte de naissance (déclaration tardive)"),
        ("p", "Pour une personne dont la naissance n'a pas été déclarée dans les délais légaux, "
              "il faut saisir le Tribunal de Grande Instance (TGI) ou la justice de paix du lieu "
              "de naissance pour obtenir un jugement supplétif. Ce jugement tient lieu d'acte "
              "de naissance à tous égards."),
        ("list", [
            "Témoins pouvant attester de la naissance.",
            "Photos d'identité du concerné.",
            "Justificatif de résidence.",
            "Pièce d'identité du demandeur ou des parents.",
        ]),
        ("h2", "Coût et délai"),
        ("list", [
            "Coût : gratuit ou timbre fiscal de 200 F CFA selon le centre d'état civil.",
            "Délai : immédiat à quelques jours pour une copie simple ; "
            "plusieurs semaines pour un jugement supplétif.",
        ]),
        ("h2", "Où faire la demande"),
        ("p", "La demande de copie d'acte de naissance se fait au centre d'état civil "
              "(mairie ou commune) du lieu de naissance. Pour un jugement supplétif, "
              "s'adresser au Tribunal de Grande Instance (TGI) ou à la justice de paix "
              "du lieu de naissance."),
        ("space", 10),
        ("source", "https://service-public.gov.bf/thematiques/etat-civil-identite-famille/"
                    "acte-de-naissance"),
    ],
)

# ---------------------------------------------------------------------------
# 6. Certificat de nationalité
# ---------------------------------------------------------------------------
build_pdf(
    "certificat_nationalite.pdf",
    "Certificat de Nationalité Burkinabè",
    [
        ("meta", "Démarche : certificat_nationalite | Mis à jour le 06/07/2026"),
        ("h2", "Description"),
        ("p", "Le certificat de nationalité burkinabè est un document officiel délivré "
              "par le Tribunal de Grande Instance (TGI) attestant qu'une personne possède "
              "la nationalité burkinabè. Il est requis pour l'établissement du passeport, "
              "de la CNIB pour les personnes nées à l'étranger, et diverses autres démarches "
              "administratives et juridiques."),
        ("h2", "Qui peut faire cette démarche ?"),
        ("p", "Tout citoyen burkinabè ou son représentant légal. Les mineurs peuvent "
              "bénéficier du certificat de nationalité par l'intermédiaire de leurs parents "
              "ou tuteur légal."),
        ("h2", "Pièces à fournir"),
        ("p", "<b>Pour les majeurs :</b>"),
        ("list", [
            "Un extrait d'acte de naissance.",
            "Une copie de la CNIB ou du passeport.",
            "Des timbres fiscaux (environ 500 F CFA).",
        ]),
        ("p", "<b>Pour les mineurs :</b>"),
        ("list", [
            "L'extrait d'acte de naissance de l'enfant.",
            "Le livret de famille des parents.",
            "La CNIB ou passeport d'un des parents.",
            "Des timbres fiscaux.",
        ]),
        ("p", "<b>Cas particulier — personne née à l'étranger :</b> fournir en plus "
              "tout document justifiant le lien de filiation avec un parent burkinabè "
              "(acte de mariage des parents, passeport du parent burkinabè, etc.)."),
        ("h2", "Validité"),
        ("p", "Le certificat de nationalité burkinabè a généralement une durée de validité "
              "de 3 à 6 mois selon l'usage auquel il est destiné. Il convient de vérifier "
              "la durée de validité requise par l'administration concernée."),
        ("h2", "Coût et délai"),
        ("list", [
            "Coût : timbres fiscaux (environ 500 F CFA).",
            "Délai : variable selon le TGI, généralement quelques jours à deux semaines.",
        ]),
        ("h2", "Où faire la demande"),
        ("p", "La demande se fait auprès du Tribunal de Grande Instance (TGI) du lieu "
              "de naissance ou de résidence du demandeur. Il est conseillé de se présenter "
              "directement au greffe du TGI compétent avec l'ensemble des pièces."),
        ("space", 10),
        ("source", "https://service-public.gov.bf/thematiques/etat-civil-identite-famille/"
                    "certificat-de-nationalite-burkinabe"),
    ],
)

print("\n6 PDFs générés dans data/pdfs/.")
