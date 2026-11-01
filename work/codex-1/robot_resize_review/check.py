import cv2
import numpy as np

h, w = 540, 640
y, x = np.indices((h, w))
images = {
    'horizontal_gradient': np.broadcast_to((y * 255 // (h-1)).astype('uint8'), (h,w)).copy(),
    'one_pixel_stripes': ((y % 2) * 255).astype('uint8'),
    'checker_8px': (((x // 8 + y // 8) % 2) * 255).astype('uint8'),
}
for name, img in images.items():
    out = cv2.resize(cv2.resize(img, (w, 528), interpolation=cv2.INTER_LINEAR), (w, h), interpolation=cv2.INTER_AREA)
    delta = img.astype(float)-out.astype(float)
    mse = np.mean(delta**2)
    psnr = float('inf') if mse == 0 else 10*np.log10(255**2/mse)
    print(f'{name}: MAE={np.mean(np.abs(delta)):.4f} levels, PSNR={psnr:.4f} dB')
print('OpenCV', cv2.__version__)
