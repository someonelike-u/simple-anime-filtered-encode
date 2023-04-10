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
from vsutil import depth, get_y
from typing import Tuple, Optional
from nnedi3_rpow2 import nnedi3_rpow2
import havsfunc as haf
from vsTAAmbk import TAAmbk
import muvsfunc as muvf
import vstools as vstools

core = vs.core
src = core.lsmas.LWLibavSource(source=file)
src16 = depth(src, 16)

def denoiseProcess(clip):
	return kgf.hybriddenoise(depth(clip, 32), 0.45, 1.5)

def rescaleProcess(clip):
	luma = get_y(clip)
	descale = kgf.inverse_scale(luma, height=nativeHeight, kernel='bicubic')
	antiAliasing = TAAmbk(depth(descale, 16), aatype='Nnedi3')
	upscale = nnedi3_rpow2(antiAliasing)
	downscale = muvf.SSIM_downsample(upscale, 1920, 1080)
	rescaled = vdf.misc.merge_chroma(depth(downscale, 16), src16)
	dehalo = haf.FineDehalo(rescaled, rx=2.4, darkstr=0.2, brightstr=0.8, thmi=44)
	dering = haf.HQDeringmod(dehalo, mthr=24, nrmode=2, sharp=0, darkthr=0)
	return dering

def debandProcess(clip):
	deband = core.neo_f3kdb.Deband(clip, y=32, cb=32, cr=32, grainy=0, grainc=0, keep_tv_range=True, output_depth=16)
	debandMask = kgf.retinex_edgemask(clip, sigma=2).std.Binarize(8500).std.Inflate()
	return core.std.MaskedMerge(deband, clip, debandMask)

def grainProcess(clip):
	return kgf.adaptive_grain(clip, static=False)

def maskCreditProcess(clip, ranges: Optional[Tuple[int, int]] = None):
	creditMask = depth(vdf.drm(depth(src16, 8), nativeHeight, thr=60, expand=6), 16)
	fixCredits = vstools.ranges.rfs(clip, core.std.MaskedMerge(clip, src16, creditMask), ranges)
	return depth(fixCredits, 10)

def filter():
	denoise = denoiseProcess(src16)
	rescale = rescaleProcess(denoise)
	deband = debandProcess(rescale)
	grain = grainProcess(deband)
	return maskCreditProcess(grain, creditRanges)

filter().set_output()
