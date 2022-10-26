#CREATED BY Scott Waters

from PIL import Image as img 
#importing Pillow library. Must be pip installed. Type "pip install Pillow" into your terminal to install


def image_crop(images, new_width): #actual cropping program. Takes a string of file names (e.g. "picture.tif, picture2.tif", and a variable for new pixel width)
    image_list = images.split(", ") #make list of image files
    print("Cropping the following: ", image_list) #user can double check files
    for image in image_list: #parses through list of images
        print("Current image: ", image) #updates user
        im = img.open(image) #open iterated file

        width, height = im.size #get image original size
        width_diff = width - new_width #finding excess pixel width

        #Image coorinates start with 0, 0 at top left corner!

        left = 0 + width_diff / 2 #remove half of excess from left side
        right = new_width + left #sets right most point to give the final pixel width away from left
        top = 0 #no height adj
        bottom = height #no height adj
        cropped_im = im.crop((left, top, right, bottom)) #generates cropped image of the defined rectangle
        period = str(image).find(".")        
        file_name = str(image)[0:period] #pulls file name to the first period
        file_type = str(image)[period:] #pulls file type (e.g. tif, JPG)
        new_name = file_name + "_cropped" + file_type #adds "cropped" and replaces file type
        cropped_im.save(new_name) #saves files
        print(new_name, " has been saved")
    print("all images cropped to ", new_width, " pixels") #completed statement
        


#user input for files
images_to_crop = input("What images files to crop? (separate using \", \"): ")
#user input for width
final_crop_width = int(input("What final pixel width? (in pixels): "))
#run program
image_crop(images_to_crop, final_crop_width)
    











