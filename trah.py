from PIL import Image
import imagehash
import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
import time

# ========== 装饰器 ==========
def execution_time_decorator(func):
    """用于装饰器，计算函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"Execution time: {time.time() - start_time:.2f}s")
        return result
    return wrapper

def compare_images(image_path1, image_path2):
    print(f"对比图片: {image_path1} 和 {image_path2}")
    
    # 方法 1: 感知哈希 (pHash)
    @execution_time_decorator
    def compare_phash(image1, image2):
        hash1 = imagehash.phash(image1)
        hash2 = imagehash.phash(image2)
        similarity = 1 - (hash1 - hash2) / len(hash1.hash.flatten())
        return similarity

    # 方法 2: 结构相似性 (SSIM)
    @execution_time_decorator
    def compare_ssim(image1, image2):
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
        score, _ = ssim(image1, image2, full=True)
        return score

    # 方法 3: 像素均方误差 (MSE)
    @execution_time_decorator
    def compare_mse(image1, image2):
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
        mse = np.mean((image1 - image2) ** 2)
        return mse

    # 加载图片
    pil_image1 = Image.open(image_path1)
    pil_image2 = Image.open(image_path2)
    
    cv_image1 = cv2.imread(image_path1, cv2.IMREAD_GRAYSCALE)
    cv_image2 = cv2.imread(image_path2, cv2.IMREAD_GRAYSCALE)

    # 计算并打印结果
    print("\n方法 1: 感知哈希 (pHash)")
    phash_similarity = compare_phash(pil_image1, pil_image2)
    print(f"相似度: {phash_similarity:.4f} (1.0 = 完全一致)")

    print("\n方法 2: 结构相似性 (SSIM)")
    ssim_similarity = compare_ssim(cv_image1, cv_image2)
    print(f"相似度: {ssim_similarity:.4f} (1.0 = 完全一致)")

    print("\n方法 3: 像素均方误差 (MSE)")
    mse_error = compare_mse(cv_image1, cv_image2)
    print(f"误差值: {mse_error:.2f} (0 = 完全一致)")


compare_images(r"after_play_5s.png", r"after_play.png")