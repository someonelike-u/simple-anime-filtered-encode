"""
Just change 3 parameters here.
"""

file = r'fileName.mkv'
nativeHeight = 837 # Use 'getNative' python module
creditRanges = [(0, 1), (2, 3)] # --> From frame 0 to frame 1, from frame 2 to frame 3, etc.

"""
The following lines can be untouched.
"""

from vstools import core, depth, join, get_y, replace_ranges
from kagefunc import inverse_scale, hybriddenoise, retinex_edgemask, adaptive_grain
from vsaa import masked_clamp_aa, upscaled_sraa, clamp_aa
from vsTAAmbk import TAAmbk
from edi_rpow2 import znedi3_rpow2
from vsscale import SSIM
from vskernels import Bicubic
from havsfunc import FineDehalo, HQDeringmod
from vsmasktools import diff_rescale

src = core.lsmas.LWLibavSource(source=file)
src16 = depth(src, 16)

def denoiseProcess(clip, strongDenoise: bool = False):
	if strongDenoise == True:
		denoise = hybriddenoise(clip, 1.2, 5)
	else:
		denoise = hybriddenoise(clip, 0.45, 1.5)
	return denoise

def rescaleProcess(clip, strongAA: bool = False, optimizedAA: bool = False):
	luma = get_y(clip)
	descale = inverse_scale(luma, height=nativeHeight, kernel='bicubic')

	if optimizedAA == True:
		AAMask = vsaa.masked_clamp_aa(descale, strength=1, opencl=False)
		strongAA = vsaa.upscaled_sraa(descale, rfactor=1.6)
		antiAliased = vsaa.clamp_aa(descale, AAMask, strongAA, strength=1.5)
	else:
		antiAliased = TAAmbk(depth(descale, 16), aatype='Eedi3' if strongAA == True else 'Nnedi3')
	upscale = znedi3_rpow2(antiAliased, 2)
	downscale = SSIM(Bicubic).scale(upscale, 1920, 1080)
	rescaled = join(depth(downscale, 16), src16)
	dehalo = FineDehalo(rescaled, rx=2.4, darkstr=0, brightstr=0.8, thmi=44)
	dering = HQDeringmod(dehalo, mthr=24, nrmode=2, sharp=0, darkthr=0)
	return dering

def debandProcess(clip, strongDeband: bool = False):
	if strongDeband == True:
		deband = core.neo_f3kdb.Deband(clip, range=16, y=48, cb=48, cr=48, grainy=0, grainc=0)
	else:
		deband = core.neo_f3kdb.Deband(clip, range=16, y=32, cb=32, cr=32, grainy=0, grainc=0)
	debandMask = retinex_edgemask(clip, sigma=2).std.Binarize(8500).std.Inflate()
	return core.std.MaskedMerge(deband, clip, debandMask)

def grainProcess(clip):
	return adaptive_grain(clip, 0.3, static=False)

def maskCreditProcess(clip, ranges = None):
	creditMask = diff_rescale(src16, nativeHeight)
	fixCredits = replace_ranges(clip, core.std.MaskedMerge(clip, src16, creditMask), ranges)
	return depth(fixCredits, 10)

def filter():
	rescale = rescaleProcess(src16)
	denoise = denoiseProcess(rescale)
	deband = debandProcess(denoise)
	grain = grainProcess(deband)
	return maskCreditProcess(grain, creditRanges)

#src16.set_output(0)
filter().set_output()
