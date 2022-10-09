import vlc

Instance = vlc.Instance()
player = Instance.media_player_new()
paused=False
# Media = Instance.media_new("/home/pablo/Escritorio/SAFE/[Accordion]Kass' Theme (The Legend of Zelda - Breath of the Wild OST)-remake!.mp3","/home/pablo/Escritorio/SAFE/Beabadoobee - Coffee.mp3")
# player.set_media(Media)
# player.play()
# time.sleep(500)
# Media = Instance.media_new("/home/pablo/Codigo/python/musica/Chernikovskaya Hata - Belaya Noch.mp3")
# player.set_media(Media)
# player.play()
# time.sleep(6)
# player.stop()



def setMedia(fileName):
    Media = Instance.media_new(fileName)
    player.set_media(Media)
    player.play()

def resume_pause(fileName):
    global paused
    try:
        f=open("mus","a")
        f.write(str(player.get_media().get_meta(0))+ " separa "+fileName+ "\n")
        f.close()
    except:
        pass
    
    if not paused:
        player.set_pause(1)
        paused=True
    else:
        paused=False
        player.set_pause(0)

