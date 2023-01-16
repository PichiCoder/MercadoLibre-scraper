import requests
from bs4 import BeautifulSoup
# lo vamos a usar para transfomar los datos y guardarlos en un excel
import pandas as pd
import datetime
import re

"""
Consideraciones al 9/1/23:
Por ejemplo si busco ps3, el primer link (de la pag 1) es este "https://listado.mercadolibre.com.ar/ps3#D[A:ps3]"
A partir de la 2da pagina es: "https://listado.mercadolibre.com.ar/consolas-videojuegos/consolas/ps3_Desde_51_NoIndex_True" 
Lo unico cambiante en la 2da pag en adelante es el nro entre Desde_ y _NoIndex, 
que va incrementando el numero 51 (pag 2) de a 50 por cada pagina. Pag 3 sera el mismo link pero con 101.
Importante: si metemos link a) o b) anda igual, nos manda a la primer pagina de resultados, lo cual nos facilita el trabajo.
a) https://listado.mercadolibre.com.ar/consolas-videojuegos/consolas/ps3_Desde_1_NoIndex_True
b) https://listado.mercadolibre.com.ar/ps3_Desde_1_NoIndex_True
Sobre todo el b) que nos abre las puertas a meter cualquier palabra en vez de ps3 para proceder con la busqueda.
"""

# Personalizamos para poner el objeto que queremos scrapear en mercadolibre.
# (Teniendo cuidado sobre como se designa en la barra de busqueda)
obj_a_buscar = input("Ingrese objeto a buscar en mercado libre:") #podemos dejar fijo un ejemplo para debuggear.
obj = (obj_a_buscar.replace(" ", "-")).lower()

# Bloque para avergiguar cuantas paginas de resultados hay.
r = requests.get(f"https://listado.mercadolibre.com.ar/{obj}_Desde_1_NoIndex_True")
soup = BeautifulSoup(r.content, features="html.parser")
# Buscamos manualmente donde esta la parte de la web donde se indica la cantidad de paginas totales
# para usar esos datos del tag, class, etc en la siguiente linea.
cantPagsResul = soup.find("li", class_="andes-pagination__page-count")
nroPags = re.findall("[0-9]+", str(cantPagsResul))
nro_final = int(nroPags[0])

# En esta variable guardamos una lista que tiene el link de cada publicacion. De cada pagina (llena) vamos a obtener 50 links.
product_links = []

"""
Ojo que en el siguiente for loop, iria range(1, nro_final+1), lo dejo como range(1, 2) para probar funcionamiento
en la 1er pag de resultados.
"""

# Este bloque es para navegar por cada una de las paginas de resultados.
x = 1
for i in range(1, 2):
    r = requests.get(f"https://listado.mercadolibre.com.ar/{obj}_Desde_{str(x)}_NoIndex_True")
    x += 50
    soup = BeautifulSoup(r.content, features="html.parser")
    # Buscamos manualmente donde esta el link, en un formato como div>class>a>href.
    # Lo hacemos inspeccionando elemento en la primer pagina de resultados.
    # Una vez que lo ubicamos, usamos el find_all, cuyos parametros elegidos filtran todos los anchor tags que tengan atributos
    # descritos a nuestra conveniencia. Asi, a_tags almacena todos los anchor tags de la pagina actual donde trabaja el for loop.
    a_tags = soup.find_all("a", class_="ui-search-item__group__element shops__items-group-details ui-search-link", href=True, title=True)
    # Otro For Loop para extraer cada uno de esos links dentro de cada atributo href="..." y guardarlo en nuestra lista.
    for link in a_tags:
        productlinks = link["href"]
        product_links.append(productlinks)

# A cont. extraemos los datos de CADA articulo, por eso nuestro objetivo era conseguir los links de cada producto!
# Esta lista contendra diccionarios. Cada uno de ellos tendra todos los datos de un producto.
productlist = []

for link in product_links:
    req = requests.get(link)
    soup = BeautifulSoup(req.content, features="html.parser")
    # Datos (usar vars en MAYUSQ primer/as letras como dato final):
    # Sobre Articulo:
    # Titulo Publicacion
    try:
        Titulo_producto = soup.find("h1", class_="ui-pdp-title").text.strip()
    except:
        Titulo_producto = "No encontrado"
    #link 1er imagen
    try:
        img = soup.find("img", class_="ui-pdp-image ui-pdp-gallery__figure__image")
        imag = re.findall("src=\"(.+?)\"", str(img))
        IMG_link = imag[0]
    except:
        IMG_link = "No obtenida"
    #Usado o Nuevo
    try:
        cond = soup.find("span", class_="ui-pdp-subtitle").text.strip()
        condi = re.findall("\w+", cond)
        Condicion = condi[0]
    except:
        Condicion = "No obtenido"
    #Precio
    try:
        Precio = soup.find("span", class_="andes-money-amount__fraction").text.strip()
    except:
        Precio = "No obtenido"
    #Sobre Vendedor
    #Nombre Vendedor
    try:
        Nombre_vendedor = soup.find("span", class_="ui-pdp-color--BLUE ui-pdp-family--REGULAR").text.strip()
    except:
        Nombre_vendedor = "No proporcionado"
    #Ubicacion vendedor
    try:
        Ubi = soup.find("p", class_="ui-seller-info__status-info__subtitle").text.strip()
    except:
        Ubi = "No encontrada"
    #Sobre atencion 
    #Calidad Atencion
    try:
        at = soup.find_all("p", class_="ui-pdp-seller__text-description")
        atencion = re.findall(">([a-zA-Z].+?)<", str(at))
        CAL_at = atencion[1]
    except:
        CAL_at = "No obtenida"
    #Al tema despacho lo tuve que poner asi porque a veces no es reconocido
    try:
        CAL_desp = atencion[2]
    except:
        CAL_desp = "No obtenida"
    #Termometro de Reputacion: 1 (Rojo, muy malo) a 5 (Verde, muy bueno).
    # Podria reemplazar CAL_desp y CAL_at
    try:
        Termo_rating = soup.find("ul", class_="ui-thermometer")["value"]
    except:
        Termo_rating = "No obtenido"
    #Cantidad de ventas del vendedor en el ultimo año
    try:
        CANT_ventas = soup.find("p", class_="ui-pdp-color--BLACK ui-pdp-size--XSMALL ui-pdp-family--REGULAR ui-pdp-seller__header__subtitle").text.strip()
    except:
        CANT_ventas = "No proporcionado"
    #Crearemos un diccionario para guardar cada dato filtrado.
    ml_data = {
        "Producto": Titulo_producto,
        "Precio": Precio,
        "Condicion": Condicion,
        "Reputacion (1 a 5)": Termo_rating,
        #"Vendedor": Nombre_vendedor,
        "Ubicacion": Ubi,
        #"Calidad_Atencion": CAL_at,
        #"Calidad_Despacho": CAL_desp,
        "Cantidad de Ventas": CANT_ventas,
        "Link": link,
        #"Imagen Link": IMG_link,   
    }
    productlist.append(ml_data)
    print("Guardando: ", ml_data["Producto"])
    
print("Carga de datos finalizada, aguarde que se genere el excel")
    
df = pd.DataFrame(productlist)
df.to_excel("ML datos.xlsx")

print("Ejecucion completada")
