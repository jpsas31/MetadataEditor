import os
import re
import shutil
from io import BytesIO
import eyed3
import requests
from PIL import Image
from PIL import ImageFile

import spotifyInfo


def changeArtist(name,fileName):
    """
    Change artist on mp3(fileName) metadata to name 
    """
    audiofile = eyed3.load(fileName)
    audiofile.tag.artist =name
    audiofile.tag.save(fileName)

def changeTitle(name,fileName):
    """
    Change title on mp3(fileName) metadata to name 
    """
    audiofile = eyed3.load(fileName)
    audiofile.tag.title = name
    audiofile.tag.save(fileName)

def changeAlbum(name,fileName):
    """
    Change album on mp3(fileName) metadata to name 
    """
    audiofile = eyed3.load(fileName)
    audiofile.tag.album = name
    audiofile.tag.save(fileName)

def albumCover(dir,link,fileName,show=False):
        
    """
    Downloads album cover from the link and saves it into mp3 file metadata     
    """
    resp = requests.get(link, stream=True)

    if(os.path.isdir(dir+"/album/")):
        os.chdir(dir+"/album/")
    else:
        os.mkdir(dir+"/album/")
        os.chdir(dir+"/album/")
        
    # Open a local file with wb ( write binary ) permission.
    local_file = open('album.jpg', 'wb')
    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    resp.raw.decode_content = True
    # Copy the response stream raw data to local image file.
    shutil.copyfileobj(resp.raw, local_file)
    # Remove the image url response object.
    del resp
    fp = open("album.jpg", 'rb')
    imageData = fp.read()
    fp.close()
    #this line avoids error on irregular block sizes of certain image files
    ImageFile.LOAD_TRUNCATED_IMAGES=True
    if(show):
        with Image.open("album.jpg") as img:
                img.show()

    os.chdir("..")

    #save album
    mySong= eyed3.load(fileName)
    if len(mySong.tag.images)==0: 
        mySong.tag.images.set(eyed3.id3.frames.ImageFrame.FRONT_COVER, imageData, 'image/jpeg')
        mySong.tag.save()


def verCover(fileName):
    """
    Displays album cover of fileName 
    """
    audio = eyed3.load(fileName)
    for imageinfo in audio.tag.images:
        with Image.open(BytesIO(imageinfo.image_data) )as img:
                ImageFile.LOAD_TRUNCATED_IMAGES=True
                img.show()
                break
               

def removeAlbumCover(fileName):
    """
    Removes album cover of fileName
    """
    audio = eyed3.load(fileName)
    for imagen in audio.tag.images:
            audio.tag._images.remove(imagen.description)
    audio.tag.save(fileName)

def songInfo(fileName):
    """
    A getter for the metadata of fileName
    """
    if(os.path.isfile(fileName)):
        audiofile = eyed3.load(fileName)
        title=audiofile.tag.title
        album=audiofile.tag.album
        artist=audiofile.tag.artist
        albumArt=len(audiofile.tag.images)

        if albumArt==0: 
            albumArt="No hay Album cover, presiona enter para buscarla automaticamente en internet y asignarla"
        else:
            albumArt="Si tiene cover"
        
        return title,album,artist,albumArt
    return "deleted","deleted","deleted","deleted"


def llenarCampos(dir,fileName=None,show=True):
    """
    Gathers fileName's metadata using spotify api and saves into the file
    """

    audiofile=eyed3.load(fileName)
    query=queryCleaner(fileName)
    
    with open('data3.txt', 'a') as outfile:
        outfile.write(query)
    
    n,ar,al,cover=spotifyInfo.get_Track_Features(query)
    if (n is None or n =="None"): n =''
    if (ar is None or ar  =="None"): ar =''
    if (al is None or al  =="None"): al =''
    if (cover is None or cover =="None"): cover =''

    audiofile=eyed3.load(fileName)
    audiofile.tag.title=n
    audiofile.tag.artist=ar
    audiofile.tag.album=al
    audiofile.tag.save()
    if(al is not None and al!="None"):
        albumCover(dir,cover,fileName,show)
     

def setCover(dir,fileName=None):
    """
    Individually sets the album cover of fileName.
    """
    audiofile = eyed3.load(fileName)
    if len(audiofile.tag.images)==0: 
            query=queryCleaner(fileName)
            n,ar,al,cover=spotifyInfo.get_Track_Features(query)
            if(al is not None and al!="None"):
                albumCover(dir,cover,fileName,show=True)
                

            
def queryCleaner(fileName):
    """
    Creates a proper query to use with the spotify api
    using filename or metadata if available.
    
    """
    audiofile = eyed3.load(fileName)
    title=audiofile.tag.title
    artist=audiofile.tag.artist
    album=audiofile.tag.album
    # with open('data3.txt', 'w') as outfile:
    #         outfile.write('\n'+"fasd "+title+artist+album)
    if(title != 'None' and title is not None):
        if(artist is not None):
            artist=artist.replace('None',"")
        elif(artist is  None):
            artist=""
        if(album  is not None):
            album=album.replace('None',"")
        elif(album is  None):
            album=""
        return ' '.join([title,artist,album]).lower()
    else: 
        query=fileName.lower()
        query=query.replace(".mp3","").replace("by","").replace("studio","").replace("live","")
        query=re.sub("\(.*?\)", "", query, flags=re.I)
        query=re.sub("20[0-9]+[0-9]+", "", query, flags=re.I)
        query=re.sub("\(.*?\)", "", query, flags=re.I)
        query=re.sub("『.*?\』", "", query, flags=re.I)
        query=re.sub("\[.*?\]", "", query, flags=re.I)
        query=re.sub("ft\.?.*", "", query, flags=re.I)
        query=re.sub("feat\.?.*", "", query, flags=re.I)
        query=re.sub("[^a-zA-Z0-9&\ ]+", ' ', query,flags=re.I)
        return query.lower()


