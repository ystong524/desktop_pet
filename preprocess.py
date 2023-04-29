from PIL import Image
import os

size = 200
src = "before"
dest = "src"

def resize_gif(path, dest, size):
    img = Image.open(path)
    img_ls = []
    for i in range(img.n_frames):
        img.seek(i)
        img_ls.append(img.copy().resize((size, size)))

    img_ls[0].save(dest, save_all=True, append_images=img_ls[1:], duration=100, loop=0)
    
for root, dirs, files in os.walk(src):
    for f in files:
        resize_gif(os.path.join(root, f),
                   os.path.join(dest, f),
                   size)
        print(f)
print("done")