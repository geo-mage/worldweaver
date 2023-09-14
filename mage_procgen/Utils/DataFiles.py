import subprocess
import os
import re

base_folder = "/home/verstraa/Work/maps/"

rendering = "rendering"

departements = "Departements/"

regions_file = "ARRONDISSEMENT/ARRONDISSEMENT.shp"

ocean_file = "OCEAN/World_Seas_IHO_v3.shp"

terrain_DB = "RGEALTI"
terrain_data_folder = "MNT"

parcellaire_DB = "PARCELLAIRE_EXPRESS"
parcellaire_data_folder = "PEPCI"
plot_file = "PARCELLE.SHP"
building_file = "BATIMENT.SHP"

bdtopo_folder = "BDTOPO"
forest_folder = "OCCUPATION_DU_SOL"
forest_file = "ZONE_DE_VEGETATION.shp"
road_folder = "TRANSPORT"
road_file = "TRONCON_DE_ROUTE.shp"
water_folder = "HYDROGRAPHIE"
water_file = "SURFACE_HYDROGRAPHIQUE.shp"
dpt_folder = "ADMINISTRATIF"
dpt_file = "ARRONDISSEMENT.shp"

shore_file = "LIMITE_TERRE_MER.shp"

texture_folder = "Textures"
texture_image_DB = "BDORTHO"
delivery = "1_DONNEES_LIVRAISON"
texture_data_folder = "OHR_RVB"

additional = "3_SUPPLEMENTS_LIVRAISON"
slab_file = "dalles.shp"

hash_file_extenstion = ".md5"

assets_folder = "Assets"

file_coords_regex = re.compile("_[0-9]{4}_[0-9]{4}_")


def setup_bdtopo(departement, archive_file):
    """
    Extracts BDTOPO archive, and changes the folders to simplify it
    from

     BDTOPO
         BDTOPO_3-3_TOUSTHEMES_SHP_LAMB93_D006_2023-06-15
             BDTOPO
                 1_DONNEES_LIVRAISON_2021-04-00084
                     BDT_3-3_SHP_LAMB93_D006-ED2023-06-15
                        OCCUPATION_DU_SOL
                            ZONE_DE_VEGETATION.shp
                        TRANSPORT
                            TRONCON_DE_ROUTE.shp
                        HYDROGRAPHIE
                            SURFACE_HYDROGRAPHIQUE.shp


     to

     BDTOPO
         1_DONNEES_LIVRAISON_2021-04-00084
            OCCUPATION_DU_SOL
                ZONE_DE_VEGETATION.shp
            TRANSPORT
                TRONCON_DE_ROUTE.shp
            HYDROGRAPHIE
                SURFACE_HYDROGRAPHIQUE.shp

    :param departement: number of the departement
    :param archive_file: archive of the database (or the first file of the split archive)
    """

    current_base_folder = os.path.join(
        base_folder, departements, str(departement), bdtopo_folder
    )

    archive_name = os.path.basename(archive_file).split(".")[0]

    out_file_option = "-o" + current_base_folder

    command_line = "7zz x " + archive_file + " " + out_file_option

    subprocess.run([command_line], shell=True)

    # BDTOPO_3-3_TOUSTHEMES_SHP_LAMB93_D006_2023-06-15
    path1 = os.path.join(current_base_folder, archive_name)

    # BDTOPO
    dir1 = os.listdir(path1)[0]
    path2 = os.path.join(path1, dir1)

    # 1_DONNEES_LIVRAISON_2021-04-00084
    # os.listdir return order is not sorted. better match by substring
    dir2 = next(x for x in os.listdir(path2) if delivery in x)
    path3 = os.path.join(path2, dir2)

    # BDT_3-3_SHP_LAMB93_D006-ED2023-06-15
    # Other file in the directory has the same name but it's the hashfile
    dir3 = next(x for x in os.listdir(path3) if hash_file_extenstion not in x)
    path4 = os.path.join(path3, dir3)

    os.makedirs(
        os.path.join(base_folder, departements, str(departement), bdtopo_folder),
        exist_ok=True,
    )
    os.rename(
        path4,
        os.path.join(
            base_folder, departements, str(departement), bdtopo_folder, delivery
        ),
    )


# TODO: delete the other folders ?
def setup_bdortho(departement, archive_file):
    """
    Extracts BDORTHO archive, and changes the folders to simplify it
    from

     BDORTHO
         ORTHOHR_1-0_RVB-0M20_JP2-E080_LAMB93_D006_2020-01-01
             ORTHOHR
                 1_DONNEES_LIVRAISON_2021-04-00084
                     OHR_RVB_0M20_JP2-E080_LAMB93_D06-2020
                         *.jp2
                 2_METADONNEES_LIVRAISON_2021-04-00084
                 3_SUPPLEMENTS_LIVRAISON_2021-04-00084
                     OHR_RVB_0M20_JP2-E080_LAMB93_D06-2020/
                         dalles.shp

     to

     BDORTHO
         1_DONNEES_LIVRAISON
             OHR_RVB
                 *.jp2
         3_SUPPLEMENTS_LIVRAISON
             OHR_RVB
                 dalles.shp

    :param departement: number of the departement
    :param archive_file: archive of the database (or the first file of the split archive)
    """

    current_base_folder = os.path.join(
        base_folder, departements, str(departement), texture_image_DB
    )

    archive_name = os.path.basename(archive_file).split(".")[0]

    out_file_option = "-o" + current_base_folder

    command_line = "7zz x " + archive_file + " " + out_file_option

    subprocess.run([command_line], shell=True)

    # ORTHOHR_1-0_RVB-0M20_JP2-E080_LAMB93_D006_2020-01-01
    path1 = os.path.join(current_base_folder, archive_name)

    # ORTHOHR
    dir1 = os.listdir(path1)[0]
    path2 = os.path.join(path1, dir1)

    # 1_DONNEES_LIVRAISON_2021-04-00084
    # os.listdir return order is not sorted. better match by substring
    dir2 = next(x for x in os.listdir(path2) if delivery in x)
    path3 = os.path.join(path2, dir2)

    # OHR_RVB_0M20_JP2-E080_LAMB93_D06-2020
    # Other file in the directory has the same name but it's the hashfile
    dir3 = next(x for x in os.listdir(path3) if hash_file_extenstion not in x)
    path4 = os.path.join(path3, dir3)

    os.makedirs(
        os.path.join(
            base_folder, departements, str(departement), texture_image_DB, delivery
        ),
        exist_ok=True,
    )
    os.rename(
        path4,
        os.path.join(
            base_folder,
            departements,
            str(departement),
            texture_image_DB,
            delivery,
            texture_data_folder,
        ),
    )

    # 3_SUPPLEMENTS_LIVRAISON_2021-04-00084
    dir4 = next(x for x in os.listdir(path2) if additional in x)
    path5 = os.path.join(path2, dir4)

    # OHR_RVB_0M20_JP2-E080_LAMB93_D06-2020
    dir5 = next(x for x in os.listdir(path5) if hash_file_extenstion not in x)
    path6 = os.path.join(path5, dir5)

    os.makedirs(
        os.path.join(
            base_folder, departements, str(departement), texture_image_DB, additional
        ),
        exist_ok=True,
    )
    os.rename(
        path6,
        os.path.join(
            base_folder,
            departements,
            str(departement),
            texture_image_DB,
            additional,
            texture_data_folder,
        ),
    )


def setup_rgealti(departement, archive_file):
    """
    Extracts RGEALTI archive, and changes the folders to simplify it
    from

     RGEALTI
         RGEALTI_2-0_1M_ASC_LAMB93-IGN69_D077_2021-03-03
             RGEALTI
                 1_DONNEES_LIVRAISON_2021-04-00084
                     RGEALTI_MNT_1M_ASC_LAMB93_IGN69_D077_20210303
                         *.asc
                 2_METADONNEES_LIVRAISON_2021-04-00084
                 3_SUPPLEMENTS_LIVRAISON_2021-04-00084
                     RGEALTI_MNT_1M_ASC_LAMB93_IGN69_D077_20210303
                         dalles.shp

     to

     RGEALTI
         1_DONNEES_LIVRAISON
             MNT
                 *.asc
         3_SUPPLEMENTS_LIVRAISON
             MNT
                 dalles.shp

    :param departement: number of the departement
    :param archive_file: archive of the database (or the first file of the split archive)
    """

    current_base_folder = os.path.join(
        base_folder, departements, str(departement), terrain_DB
    )

    archive_name = os.path.basename(archive_file).split(".")[0]

    out_file_option = "-o" + current_base_folder

    command_line = "7zz x " + archive_file + " " + out_file_option

    subprocess.run([command_line], shell=True)

    # RGEALTI_2-0_1M_ASC_LAMB93-IGN69_D077_2021-03-03
    path1 = os.path.join(current_base_folder, archive_name)

    # RGEALTI
    dir1 = os.listdir(path1)[0]
    path2 = os.path.join(path1, dir1)

    # 1_DONNEES_LIVRAISON_2021-04-00084
    # os.listdir return order is not sorted. better match by substring
    dir2 = next(x for x in os.listdir(path2) if delivery in x)
    path3 = os.path.join(path2, dir2)

    # RGEALTI_MNT_1M_ASC_LAMB93_IGN69_D077_20210303
    # Folder contains 3 subfolders, and the corresponding hashfiles.
    dirs3 = [x for x in os.listdir(path3) if hash_file_extenstion not in x]
    dir3 = next(x for x in dirs3 if terrain_data_folder in x)
    path4 = os.path.join(path3, dir3)

    os.makedirs(
        os.path.join(base_folder, departements, str(departement), terrain_DB, delivery),
        exist_ok=True,
    )
    os.rename(
        path4,
        os.path.join(
            base_folder,
            departements,
            str(departement),
            terrain_DB,
            delivery,
            terrain_data_folder,
        ),
    )

    # 3_SUPPLEMENTS_LIVRAISON_2021-04-00084
    dir4 = next(x for x in os.listdir(path2) if additional in x)
    path5 = os.path.join(path2, dir4)

    # RGEALTI_MNT_1M_ASC_LAMB93_IGN69_D077_20210303
    dir5 = next(x for x in os.listdir(path5) if hash_file_extenstion not in x)
    path6 = os.path.join(path5, dir5)

    os.makedirs(
        os.path.join(
            base_folder, departements, str(departement), terrain_DB, additional
        ),
        exist_ok=True,
    )
    os.rename(
        path6,
        os.path.join(
            base_folder,
            departements,
            str(departement),
            terrain_DB,
            additional,
            terrain_data_folder,
        ),
    )


# TODO: delete the other folders ?
def setup_parcellaire(departement, archive_file):
    """
    Extracts PARCELLAIRE_EXPRESS archive, and changes the folders to simplify it
    from

     PARCELLAIRE_EXPRESS
         PARCELLAIRE_EXPRESS_1-1__SHP_LAMB93_D006_2023-04-01
             PARCELLAIRE_EXPRESS
                 1_DONNEES_LIVRAISON_2021-04-00084
                     PEPCI_1-1_SHP_LAMB93_D006
                         BATIMENT.SHP
                         PARCELLE.SHP

     to

     PARCELLAIRE_EXPRESS
         1_DONNEES_LIVRAISON
             PEPCI
                BATIMENT.SHP
                PARCELLE.SHP

    :param departement: number of the departement
    :param archive_file: archive of the database (or the first file of the split archive)
    """

    current_base_folder = os.path.join(
        base_folder, departements, str(departement), parcellaire_DB
    )

    archive_name = os.path.basename(archive_file).split(".")[0]

    out_file_option = "-o" + current_base_folder

    command_line = "7zz x " + archive_file + " " + out_file_option

    subprocess.run([command_line], shell=True)

    # PARCELLAIRE_EXPRESS_1-1__SHP_LAMB93_D006_2023-04-01
    path1 = os.path.join(current_base_folder, archive_name)

    # PARCELLAIRE_EXPRESS
    dir1 = os.listdir(path1)[0]
    path2 = os.path.join(path1, dir1)

    # 1_DONNEES_LIVRAISON_2021-04-00084
    # os.listdir return order is not sorted. better match by substring
    dir2 = next(x for x in os.listdir(path2) if delivery in x)
    path3 = os.path.join(path2, dir2)

    # PEPCI_1-1_SHP_LAMB93_D006
    # Other file in the directory has the same name but it's the hashfile
    dir3 = next(x for x in os.listdir(path3) if hash_file_extenstion not in x)
    path4 = os.path.join(path3, dir3)

    os.makedirs(
        os.path.join(
            base_folder, departements, str(departement), parcellaire_DB, delivery
        ),
        exist_ok=True,
    )
    os.rename(
        path4,
        os.path.join(
            base_folder,
            departements,
            str(departement),
            parcellaire_DB,
            delivery,
            parcellaire_data_folder,
        ),
    )
