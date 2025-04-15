"""Creates a .dot file that shows
- the links between classes
    if there is a triple (s p o) with (s a C) and (o a D) there is a link C -p-> D
- the ‘attributes’ of the classes
    if there is a triple (s p o) with (s a C) and o a literal then p is an attribute of C
- the prefixes of the class instances
    if we have (<http://path#xxx> a C) or (<http://path/xxx> a C) (without #) then
    <http://path#> or <http://path/> is an instance prefix of C

Use:

% python3 path-to-rdf-viz.py graph-location prefix-file

where graph-location is either the name of a file that contains and RDF graph
or the URL of an RDF graph stored at a SPARQL endpoint, e.g. http://localhost:7200/repositories/fds

output the .dot representation on the standard output

"""

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS

import sys
import re
import json

invprefixes = {
'http://www.openrdf.org/schema/sesame#' : 'sesame' ,
'http://www.w3.org/1999/02/22-rdf-syntax-ns#' : 'rdf' ,
'http://www.w3.org/2000/01/rdf-schema#' : 'rdfs' ,
'http://purl.org/dc/elements/1.1/' : 'dc' ,
'http://purl.org/dc/terms/' : 'dct' ,
'http://www.w3.org/2002/07/owl#' : 'owl' ,
'http://www.w3.org/2001/XMLSchema#' : 'xsd' ,
'http://www.w3.org/XML/1998/namespace' : 'xml' ,
'http://www.w3.org/2004/02/skos/core#' : 'skos' ,
 }

def prefixize(uri:str) -> str :
    puri = uri
    for v in invprefixes:
        if uri.startswith(v) : return puri.replace(v, invprefixes[v]+':')
    return puri

def extractprefix(uri:str) -> str :
    if '#' in uri:
        return uri.split('#')[0] + '#'
    else:
        return re.sub('/[^/]+$','/', uri)

np = Namespace("http://unige.ch/rcnum/")
g = Graph()

service = ''
if sys.argv[1].startswith('http://'):
    service = f'SERVICE <{sys.argv[1]}> '
else:
    g.parse(sys.argv[1])


g.bind('rdf', RDF)

if len(sys.argv) > 1:
    f = open(sys.argv[2])
    content = f.read()
    prefixes = json.loads(content)
else:
    prefixes = {}

for p in prefixes:
    invprefixes[prefixes[p]] = p


# Find the class links

qref =  f"""
            SELECT DISTINCT ?x ?p ?z
            WHERE {{
                {service}
                {{ ?s rdf:type ?x. ?o rdf:type ?z . ?s ?p ?o.  FILTER(! ISBLANK(?z) )
            }}
            }}
            """
qrefres = g.query(qref) 

clsloop = {}
for r in qrefres:
    n1 = prefixize(r.x)
    n2 = prefixize(r.z)
    lab = prefixize(r.p)
    if n1 == n2 :
        clsloop[n1] = clsloop[n1] + '\n' + lab if n1 in clsloop else lab
    else:
        print(f'  "{n1}" -> "{n2}" [label = "{lab}"] ;')

for c in clsloop:
    print(f'  "{c}" -> "{c}" [label = "{clsloop[c]}"] ;')


# Class attributes

qref =  f"""
            SELECT DISTINCT ?x ?p 
            WHERE {{ 
                {service}
                {{ ?s rdf:type ?x. ?s ?p ?o.  FILTER(ISLITERAL(?o) ) }}
            }}
            """
qrefres = g.query(qref)
clsdict = {}

for r in qrefres:
    cls = prefixize(r.x)
    if cls in clsdict:
        clsdict[cls] = clsdict[cls] + '\\n' + prefixize(r.p)
    else:
        clsdict[cls] = prefixize(r.p)

for c in clsdict :
    print(f'"{c}" [label="{{{c} |{clsdict[c]}}}"] ;')



# Instance prefixes

qref =  f"""
            SELECT DISTINCT ?i ?c 
            WHERE {{ 
                {service}
                {{ ?i rdf:type ?c. }}
            }}
            """
qrefres = g.query(qref)
instdict = {}

for r in qrefres:
    pfx = extractprefix(r.i)
    cls = prefixize(r.c)
    if pfx not in instdict:
        instdict[pfx] = set()
    instdict[pfx].add(cls)

for pf in instdict :
    for c in instdict[pf] :
        print(f'"{pf}" -> " {c}" ;')