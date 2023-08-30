pandoc ./beamformer_framework_pandoc.tex -f latex+raw_tex  \
    --citeproc --bibliography paper/ref.bib \
    -F ./pandoc-vanvliet.py \
    --resource-path ./paper \
    --reference-doc template.docx \
    -o beamformer_framework.docx
