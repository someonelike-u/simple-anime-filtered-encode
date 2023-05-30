"""
Just change 3 parameters here.
"""

file = r'fileName.mkv'
nativeHeight = 720 # Use 'getNative' python module
creditRanges = [(0, 1), (2, 3)] # --> From frame 0 to frame 1, from frame 2 to frame 3, etc.

"""
The following lines can be untouched.
"""

import vapoursynth as vs
import kagefunc as kgf
import vardefunc as vdf
from vstools import depth, get_y, replace_ranges
from nnedi3_rpow2 import nnedi3_rpow2
import havsfunc as haf
from vsTAAmbk import TAAmbk
import muvsfunc as muvf
import vsaa

core = vs.core
src = core.lsmas.LWLibavSource(source=file)
src16 = depth(src, 16)

def denoiseProcess(clip, strongDenoise: bool = False):
	if strongDenoise == True:
		denoise = kgf.hybriddenoise(clip, 1.2, 5)
	else:
		denoise = kgf.hybriddenoise(clip, 0.45, 1.5)
	return denoise

def rescaleProcess(clip, strongAA: bool = False, optimizedAA: bool = False):
	luma = get_y(clip)
	descale = kgf.inverse_scale(luma, height=nativeHeight, kernel='bicubic')

	if optimizedAA == True:
		AAMask = vsaa.masked_clamp_aa(descale, strength=4, opencl=False)
		AA = vsaa.upscaled_sraa(descale, rfactor=1.6)
		antiAliasing = vsaa.clamp_aa(descale, AAMask, AA, strength=2)
	else:
		antiAliasing = TAAmbk(depth(descale, 16), aatype='Eedi3' if strongAA == True else 'Nnedi3')
	upscale = nnedi3_rpow2(antiAliasing)
	downscale = muvf.SSIM_downsample(upscale, 1920, 1080)
	rescaled = vdf.misc.merge_chroma(depth(downscale, 16), src16)
	dehalo = haf.FineDehalo(rescaled, rx=2.4, darkstr=0.2, brightstr=0.8, thmi=44)
	dering = haf.HQDeringmod(dehalo, mthr=24, nrmode=2, sharp=0, darkthr=0)
	return dering

def debandProcess(clip, strongDeband: bool = False):
	if strongDeband == True:
		deband = core.neo_f3kdb.Deband(clip, range=16, y=48, cb=48, cr=48, grainy=0, grainc=0, keep_tv_range=True, sample_mode=4, output_depth=16)
	else:
		deband = core.neo_f3kdb.Deband(clip, range=16, y=32, cb=32, cr=32, grainy=0, grainc=0, keep_tv_range=True, sample_mode=4, output_depth=16)
	debandMask = kgf.retinex_edgemask(clip, sigma=2).std.Binarize(8500).std.Inflate()
	return core.std.MaskedMerge(deband, clip, debandMask)

def grainProcess(clip):
	return kgf.adaptive_grain(clip, static=False)

def maskCreditProcess(clip, ranges = None):
	creditMask = depth(vdf.drm(depth(src16, 8), nativeHeight, thr=60, expand=6), 16)
	fixCredits = replace_ranges(clip, core.std.MaskedMerge(clip, src16, creditMask), ranges)
	return depth(fixCredits, 10)

def filter():
	rescale = rescaleProcess(src16)
	denoise = denoiseProcess(rescale)
	deband = debandProcess(denoise)
	grain = grainProcess(deband)
	return maskCreditProcess(grain, creditRanges)

filter().set_output()
