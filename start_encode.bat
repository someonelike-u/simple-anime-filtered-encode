@ECHO OFF

set fileName="simple_filtered_encode"
set vspipe="D:\VapourSynth64Portable\VapourSynth64\vspipe.exe"
set python="D:\VapourSynth64Portable\VapourSynth64\python.exe"
set x265="D:\VapourSynth64Portable\bin\x265.exe"
set params="--preset slower --rd 4 --no-rect --no-amp --rskip 0 --tu-intra-depth 2 --tu-inter-depth 2 --no-tskip --merange 57 --subme 5 --b-intra --weightb --no-rect --no-amp --no-strong-intra-smoothing --psy-rd 2.0 --psy-rdoq 2.0 --no-open-gop --no-cutree --keyint 240 --min-keyint 23 --ref 6 --scenecut 40 --rc-lookahead 60 --bframes 16 --aq-mode 3 --aq-strength 0.85 --cbqpoffs -2 --crqpoffs -2 --qcomp 0.75 --deblock=-2:-2 --no-sao --no-sao-non-deblock --sar 1 --range limited --colorprim 1 --transfer 1 --colormatrix 1 --output-depth 10"

echo [Info] Start encode: %fileName%
%vspipe% -c y4m "scripts\%fileName%.vpy" - | %x265% --y4m %params% --crf 15 --output "%fileName%.265" -

pause
