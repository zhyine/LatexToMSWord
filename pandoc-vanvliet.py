import os
import sys
import re
import subprocess
from panflute import *

def first_str(elem):
    """
    Helper function that returns the first Str() node under the given element.
    """
    if hasattr(elem, 'content'):
        for child in elem.content:
            if isinstance(child, Str):
                return(child)
            else:
                t = first_str(child)
                if t is not None:
                    return t
    return None

def add_space_to_citation(elem, doc):
    """
    In the template, we use the \cite{} command without any preceding space.
    When converting with pandoc, we need to add this space.
    """
    if isinstance(elem, Cite):
        t = first_str(elem)
        if t is not None and t.text.startswith('('):
            t.text = '\u00a0' + t.text  # prepend a non-breaking space
            
def rasterize_pdf_images(elem, doc):
    """
    Rasterize PDF images to PNG with a reasonable resolution.
    """
    if isinstance(elem, Image):
        print('Rasterizing', elem.url, file=sys.stderr)
        if elem.url.endswith('.pdf'):
            url_png = 'paper/' + elem.url.replace('.pdf', '.png')
            if not os.path.exists(url_png):
                subprocess.run(['pdftoppm',
                                '-scale-to', '1024',
                                '-png',
                                '-singlefile',
                                f'paper/{elem.url}',
                                f'paper/{elem.url[:-4]}'])
            elem.url = url_png
        # Remove any width annotations made in the LaTeX file, which Word
        # cannot handle, so the width defaults to the pagewidth.
        if 'width' in elem.attributes:
            del elem.attributes['width']

    return elem

figures = {}
tables = {}
def number_float(elem, doc):
    """
    Figures and Tables (that are floats in LaTeX) need to be given a proper number.
    This function also keeps track of them in a global dictionary (defined at
    the top of this file) so we can later resolve \autoref{} calls properly.
    """
    if isinstance(elem, Image):
        fignum = f'Figure {len(figures) + 1}'
        figures[elem.identifier] = fignum
        t = first_str(elem)
        t = fignum + ': ' + str(t)
        return elem
    elif isinstance(elem, Table):
        tabnum = f'Table {len(tables) + 1}'
        tables[elem.parent.identifier] = tabnum
        t = first_str(elem.caption)
        t = tabnum + ': ' + str(t)
        return elem


autoref_pattern = re.compile(r"\\autoref\{(...):(.*)\}")
def resolve_autoref(elem, doc):
    """
    Do \autoref{} manually.
    """
    if isinstance(elem, RawInline):
        matches = autoref_pattern.match(elem.text)
        if matches:
            float_type = matches.group(1)
            identifier = float_type + ':' + matches.group(2)
            if float_type == 'fig' and identifier in figures:
                return Str(figures[identifier])
            elif float_type == 'tab' and identifier in tables:
                return Str(tables[identifier])

def load_acronyms():
    """
    In order to deal with acronyms, we need to load and parse the acronyms.tex manually.
    """
    pattern = re.compile(r"\\newacronym(\[.*\])?\{(?P<label>[A-Za-z]+)\}\{.+\}\{(?P<value>[A-Za-z 0-9\-]+)\}")
    
    with open('paper/acrynyms.tex', 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                acronyms[match.group('label')] = match.group('value')
                
def resolve_acronyms(elem, doc):
    """
    In the template, we use \gls{TIL} to denote acronyms. These need to be
    expended upon first use.
    """
    if isinstance(elem, Span) and "acronym-label" in elem.attributes:
        label = elem.attributes["acronym-label"]
        
        if label in acronyms:
            # this is the case: "singular" in form and "long" in form:
            value = acronyms[label]
            
            form = elem.attributes["acronym-form"]
            if label in refcounts and "short" in form:
                if "singular" in form:
                    value = label
                else:
                    value = label + "s"
            
            elif "full" in form or "short" in form:
                # remember that label has been used
                if "short" in form:
                    refcounts[label] = True
                
                if "singular" in form:
                    value = value + " (" + label + ")"
                else:
                    value = value + "s (" + label + "s)"
            
            elif "abbrv" in form:
                if "singular" in form:
                    value = label
                else:
                    value = label + "s"
            
            return Span(Str(value))

def main(doc=None):
    """Run all the filters on the AST."""
    return run_filters([
        resolve_acronyms,
        add_space_to_citation,
        number_float,
        resolve_autoref,
        rasterize_pdf_images,
    ], doc=doc)

if __name__ == "__main__":
    main()
