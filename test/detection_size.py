import numpy as np

def arcmin_to_radians(arcmin):
    # 1 arcmin = 1/60 degree
    # degree to rad: rad = deg * (pi/180)
    degrees = arcmin / 60.0
    radians = degrees * (np.pi / 180.0)
    return radians

# 시력 1.0 기준 각분해능 (1 arcminute)
theta = arcmin_to_radians(25.0)

# 예시 intrinsic matrix
# fx, fy는 보통 단위: 픽셀
K = np.array([[600.0,    0.0, 640.0],
              [   0.0, 600.0, 360.0],
              [   0.0,    0.0,   1.0]])

fx = K[0,0]  # focal length in pixels (x축 기준)

# 1 arcminute 각도를 갖는 대상을 이미지 상에서 몇 픽셀로 표현되는지 계산
pixel_size = fx * theta

print("1 arcminute 각분해능에 해당하는 픽셀 단위:", pixel_size, "픽셀")
