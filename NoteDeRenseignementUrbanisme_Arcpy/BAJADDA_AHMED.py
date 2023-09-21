from arcpy import *
from numpy import *
from fpdf import FPDF
import os

#if the output data already exists, it will be overwritten with the new output without warning
env.overwhriteOutput=True


dateDemande=GetParameterAsText(0)
nom_Demandeur=GetParameterAsText(2)
numeroDemande=GetParameterAsText(1)
txtFile=GetParameterAsText(3)



env.workspace=r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\BAJADDA_AHMED.mdb"


#la creation de la couche parcelle avec le meme  système de projection SRC des couches de la GDB 
SRC=Describe(os.path.join(env.workspace,'communes')).spatialReference
parcelle = CreateFeatureclass_management(env.workspace,"Parcelle","POLYGON",spatial_reference=SRC)


#sauvgarder les coordonnées des points entrées par l'utilisateur(fichier texte) dans un Array
with open(txtFile,'r') as f:
    A=Array()
    for ligne in f.readlines()[1:]:
        ID,X,Y = ligne.split(';')
        A.append(Point(float(X),float(Y)))
        
        
#remplir la couche parcelle apartir des points donnes par l'utilisateur
with da.InsertCursor(parcelle,["Shape@"])as cursor:
        cursor.insertRow([Polygon(A)])
 

#la surface totale de la parcelle constituée par l'utilisateur
with da.SearchCursor(parcelle,["shape@Area"]) as cursor:
    for row in cursor:
        surfaceParcelle=row[0]
        
        
        
#intersection de la "parcelle" et "zonage"
Intersect_analysis ([parcelle,"zonage"], "parcelleXzonage")


#calculer la surface d'intersection
surfaceIntersection=0
with da.SearchCursor("parcelleXzonage",["shape@Area"]) as cursor:
    for row in cursor:
        surfaceIntersection += row[0]
       
        
Secteurs=[] 
Zones=[]   
with da.SearchCursor("parcelleXzonage",["SECTEUR","ZONE_","Shape_Area"]) as cursor:
    for row in cursor:
        Secteurs.append([row[0],row[2]])
        Zones.append([row[1],row[2]])
 
       
#intersection de la "parcelle" et "communes"     
Intersect_analysis ([parcelle,"communes"], "parcelleXcommunes")

communes=[]
with da.SearchCursor("parcelleXcommunes",["Nom","Shape_Area"]) as cursor:
    for row in cursor:
        communes.append([row[0],row[1]])
        
print(Secteurs)
print(Zones)

#réorganiser les informations du zonage pour eviter les doublons: 
def organiser_list(liste) : 
    L = []
    L2 = []
    for i in range(len(liste)) :
        if liste[i][0] not in L2 : 
            L2.append(liste[i][0])
            L.append(liste[i])
        else : 
            for j in range(len(L)) :
                if L[j][0] == liste[i][0] : 
                    L[j][1] += liste[i][1]
    return L


Secteurs = organiser_list(Secteurs)
Zones = organiser_list(Zones)
communes = organiser_list(communes)


#On passe maintennant à la création du fichier mxd qui nous permettra d'obtenir le résultat de zonage : 
#on va travailler avec le fichier mxd ouvert lors d l'éxécution du script



mxd=mapping.MapDocument(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\BAJADDA_AHMED.mxd")


data_fr = arcpy.mapping.ListDataFrames(mxd)


layer1 = arcpy.mapping.Layer(os.path.join(env.workspace,"communes"))
layer2 = arcpy.mapping.Layer(os.path.join(env.workspace,"Parcelle"))
mapping.AddLayer(data_fr[0],layer1,"AUTO_ARRANGE")
mapping.AddLayer(data_fr[0],layer2,"AUTO_ARRANGE")


for layer in mapping.ListLayers(mxd):    
        layer.visible=True
   
mapping.ExportToJPEG(mxd,r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\\DataFrame.jpg')

#les valeurs par défaut: les pages de pdf en portrait A4 et l'unité de mesure est le millimètre
if int(surfaceIntersection)==int(surfaceParcelle):
       pdf=FPDF('P','mm','A4')
       pdf.add_page()
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\log_EHTP.png',45,17,130,32)
       pdf.set_font('arial','', 11)
       pdf.set_text_color(170,0,0)
       vv= "                                                                                                             "+dateDemande
       pdf.ln(45)
       pdf.cell(0, 5, vv )
       pdf.set_font('arial','', 11)
       pdf.set_text_color(0,0,0)
       pdf.ln(10)
       pdf.cell(0, 5, '                                                                                    A' )
       pdf.ln(8)
       pdf.cell(0, 5, '                                                              M/Mme '+nom_Demandeur)
       pdf.ln(15)
       pdf.cell(0, 5,"          Objet : Note de renseignements urbanistiques indicative relative a votre demande N")
       pdf.ln(5)
       pdf.cell(0, 5,"          "+numeroDemande )
       pdf.ln(15)
       pdf.cell(0, 5,"           En reponse a votre demande citee en objet, j ai l honneur de vous faire connaitre que d apres")
       pdf.ln(5)
       pdf.cell(0, 5,"           les dispositions des documents d urbanisme, le terrain en question d une superficie "+str(surfaceParcelle))
       pdf.ln(5)
       pdf.cell(0, 5,"           m2 et appartenant a la commune / arrondissement "+communes[0][0])
       pdf.ln(5)
       pdf.cell(0, 5,"           est affecte comme suit:")
       pdf.ln(5)
       pdf.cell(0, 5,"                  - Situe en zone :")
       pdf.ln(5)
       for zone in Zones:
            pdf.cell(0, 5,"                    - "+zone[0]+"                    - superficie:"+str(zone[1])+"m2")
            pdf.ln(5)
       pdf.cell(0, 5,"                  - En secteur:")
       pdf.ln(5)
       for secteur in Secteurs:
            pdf.cell(0, 5,"                    - "+secteur[0]+"                    - superficie:"+str(secteur[1])+"m2")
            pdf.ln(5)
       pdf.ln(10)
       pdf.cell(0, 5,"            De meme, vous trouverez ci-joint un extrait du document d urbanisme. ")
       pdf.ln(5)
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\DataFrame.jpg',w=160, h=120)
       pdf.ln(5)
       pdf.cell(0, 5,"           Veuillez agreer, M/Mme, l expression de mes salutations distinguees.")
       pdf.ln(15)
       pdf.cell(0, 5,"                                                  Signature")
       pdf.image(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\signature.png",x=45,w=110,h=29)
       pdf.output(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\NRU_modele1.pdf")

   
s=str(surfaceParcelle)
if surfaceIntersection==0:
       pdf=FPDF('P','mm','A4')
       pdf.add_page()
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\log_EHTP.png',45,17,130,32)
       pdf.set_font('arial','', 11)
       pdf.set_text_color(170,0,0)
       vv= "                                                                                                             "+dateDemande
       pdf.ln(45)
       pdf.cell(0, 5, vv )
       pdf.set_font('arial','', 11)
       pdf.set_text_color(0,0,0)
       pdf.ln(10)
       pdf.cell(0, 5, '                                                                                    A' )
       pdf.ln(8)
       pdf.cell(0, 5, '                                                              M/Mme '+nom_Demandeur )
       pdf.ln(15)
       pdf.cell(0, 5,"          Objet : Note de renseignements urbanistiques indicative relative a votre demande N")
       pdf.ln(5)
       pdf.cell(0, 5,"          "+numeroDemande )
       pdf.ln(15)
       pdf.cell(0, 5,"           En reponse a votre demande citee en objet, j ai l honneur de vous faire connaitre que d apres")
       pdf.ln(5)
       pdf.cell(0, 5,"           les dispositions des documents d urbanisme, le terrain en question d une superficie "+s)
       pdf.ln(5)
       pdf.cell(0, 5,"            m2 est situe dans une zone non couverte par un document durbanisme.")
       pdf.ln(10)
       pdf.cell(0, 5,"           De meme, vous trouverez ci-joint un extrait montrant la position du terrain par rapport")
       pdf.ln(5)
       pdf.cell(0, 5,"           a la limite couverte par des documents durbanisme.")
       pdf.ln(5)
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\DataFrame.jpg',w=160, h=120)
       pdf.ln(60)
       pdf.cell(0, 5,"           Veuillez agreer, M/Mme, l expression de mes salutations distinguees.")
       pdf.ln(15)
       pdf.cell(0, 5,"                                                  Signature")
       pdf.image(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\signature.png",x=45,w=110,h=29)
       pdf.output(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\NRU_modele2.pdf")



if int(surfaceIntersection)<int(surfaceParcelle) and surfaceIntersection!=0 :
       pdf=FPDF('P','mm','A4')
       pdf.add_page()
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\log_EHTP.png',45,17,130,32)
       pdf.set_font('arial','', 11)
       pdf.set_text_color(170,0,0)
       vv= "                                                                                                             "+dateDemande
       pdf.ln(45)
       pdf.cell(0, 5, vv )
       pdf.set_font('arial','', 11)
       pdf.set_text_color(0,0,0)
       pdf.ln(10)
       pdf.cell(0, 5, '                                                                                    A' )
       pdf.ln(8)
       pdf.cell(0, 5, '                                                              M/Mme '+nom_Demandeur)
       pdf.ln(15)
       pdf.cell(0, 5,"          Objet : Note de renseignements urbanistiques indicative relative a votre demande N")
       pdf.ln(5)
       pdf.cell(0, 5,"          "+numeroDemande )
       pdf.ln(15)
       pdf.cell(0, 5,"           En reponse a votre demande citee en objet, j ai l honneur de vous faire connaitre que d apres")
       pdf.ln(5)
       pdf.cell(0, 5,"           les dispositions des documents d urbanisme, le terrain en question d une superficie "+str(surfaceParcelle))
       pdf.ln(5)
       pdf.cell(0, 5,"           m2 et appartenant a la commune / arrondissement "+communes[0][0])
       pdf.ln(5)
       pdf.cell(0, 5,"           est situe sur la limite des documents d urbanisme (DU).")
       pdf.ln(8)
       pdf.cell(0, 5,"           La partie du terrain situee a l interieur des DU d une superficie de "+str(surfaceIntersection)+" m2")
       pdf.ln(5)
       pdf.cell(0, 5,"           est affecte comme suit:")
       pdf.ln(8)
       pdf.cell(0, 5,"                  - Situe en zone :")
       pdf.ln(5)
       for zone in Zones:
            pdf.cell(0, 5,"                    - "+zone[0]+"                    - superficie: "+str(zone[1])+"m2")
            pdf.ln(5)
       pdf.cell(0, 5,"                  - En secteur:")
       pdf.ln(5)
       for secteur in Secteurs:
            pdf.cell(0, 5,"                    - "+secteur[0]+"                    - superficie: "+str(secteur[1])+"m2")
            pdf.ln(5)
       pdf.ln(8)
       pdf.cell(0, 5,"           L autre partie d une superficie "+str(surfaceParcelle - surfaceIntersection)+" m2 est situe hors")
       pdf.ln(5)
       pdf.cell(0, 5,"           document d urbanisme.")
       pdf.ln(8)
       pdf.cell(0, 5,"           De meme, vous trouverez ci-joint un extrait du document d urbanisme. ")
       pdf.ln(5)
       pdf.image(r'C:\Users\PC\Desktop\Mini_Projet_Arcpy\DataFrame.jpg',w=160, h=120)
       pdf.ln(5)
       pdf.cell(0, 5,"           Veuillez agreer, M/Mme, l expression de mes salutations distinguees.")
       pdf.ln(15)
       pdf.cell(0, 5,"                                                  Signature")
       pdf.image(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\signature.png",x=45,w=110,h=29)
       pdf.output(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\NRU_modele3.pdf")
Delete_management(r"C:\Users\PC\Desktop\Mini_Projet_Arcpy\DataFrame.jpg")
Delete_management(os.path.join(env.workspace,"parcelleXzonage"))
Delete_management(os.path.join(env.workspace,"parcelleXcommunes"))