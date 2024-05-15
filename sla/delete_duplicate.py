""""
Script (function) to delete duplicate images with the same aquitision date
It create a property to select duplicated images and filter the collection


"""


import ee


def no_duplicate(image_collection):
#Generate a List to compare dates
    lista = image_collection.toList(image_collection.size())

    imagen = ee.Image(lista.get(0))
#Add in the end of the list a dummy image
    lista = lista.add(imagen)

# Function to map along the image collection
    def find_duplicate(image):
        isduplicate = ee.String('')
        numero = lista.indexOf(image)
        image1 = ee.Image(lista.get(numero.add(1)))
        #Compare the image(0) in the ImageCollection with the image(1) in the List
        date1 = image.date().format('Y-M-d')
        date2 = image1.date().format('Y-M-d')
        state = ee.Algorithms.IsEqual(date1,date2)
        isduplicate = ee.String(ee.Algorithms.If(state,'duplicate','nonduplicate'))
        # retun the property 'same_date' used to filter the image collection
        return image.set({'same_date': isduplicate})
    
    # applt the function
    image_collection = image_collection.map(find_duplicate)
    # filter the image collection
    no_duplicate_final = image_collection.filter(ee.Filter.eq('same_date','nonduplicate'))
    
    return no_duplicate_final
