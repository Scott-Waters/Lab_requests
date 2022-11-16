#CREATED BY Scott Waters

from PIL import Image as img
import glob 
#importing Pillow library. Must be pip installed. Type "pip install Pillow" into your terminal to install


def image_crop(images, new_width): #actual cropping program. Takes a list of file names and a variable for new pixel width)
    
    print("Cropping the following: ", images) #user can double check files
    for image in images: #parses through list of images
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
        
def main():

    file_type = input("What is your file extension? (e.g. \".tif, .png, etc\"): ")
    #gathers all .X files from directory
    print("All available {} files in folder have been input".format(file_type))
    file_list = [i for i in glob.glob('*{}'.format(file_type))]
    #removes files that were unwanted
    remove_files = input("Do you need to remove files? (Y/N): ")
    remove_files = remove_files.upper()
    if remove_files == 'Y':
        to_remove = input("What files do you want to remove? (separate by \", \") (can be one or multiple) : ")
        remove_list = to_remove.split(", ")
        for each in remove_list:
            print("removing :", each)
            file_list.remove(each)
            print(each, " has been removed")
        
    #user input for width
    final_crop_width = int(input("What final pixel width? (in pixels): "))
    #run program
    image_crop(file_list, final_crop_width)
        
if __name__ == "__main__":
    main()











