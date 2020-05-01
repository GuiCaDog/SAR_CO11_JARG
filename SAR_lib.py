import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import time
import math
import operator
#-------------NOMBRES---------------
#-----Andreu Casamayor Segarra------
#-----Jose Javier Calvo Moratilla---   
#-----Raül Perelló Pinazo-----------
#-----Guillem Calabuig Domenech-----
#-----------------------------------

class SAR_Project:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de noticias
        
        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm + ranking de resultado

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """
    
    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [("title", True), ("date", False),
              ("keywords", True), ("article", True),
              ("summary", True)]
    
    
    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10


    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas 

        """
        self.index = {
            'article': {},
            'title': {},
            'summary': {},
            'keywords': {},
            'date': {}

        } # hash para el indice invertido de terminos --> clave: termino, valor: posting list.
                        # Si se hace la implementacion multifield, se puede hacer un segundo nivel de hashing de tal forma que:
                        # self.index['title'] seria el indice invertido del campo 'title'.
        
        self.sindex = {
            'article': {},
            'title': {},
            'summary': {},
            'keywords': {},
            'date': {}
        } # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {} # hash para consulta->permuterms.
        self.pterms = []
        self.permToToken={} #hash para permuterm->token
        self.permFieldCount = {
            'article': 0,
            'title': 0,
            'summary': 0,
            'keywords': 0,
            'date': 0
        }
        self.docs = {} # diccionario de terminos --> clave: entero(docid),  valor: ruta del fichero.
        self.weight = {
            'article': {},
            'title': {},
            'summary': {},
            'keywords': {},
            'date': {}
            } # hash de terminos para el pesado, ranking de resultados. puede no utilizarse
        self.termFreq = {} 
        self.news = {} # hash de noticias --> clave entero (newid), valor: la info necesaria para diferenciar la noticia dentro de su fichero
        self.tokenizer = re.compile("\W+") # expresion regular para hacer la tokenizacion
        self.elimina = re.compile("[AND|OR]")
        self.stemmer = SnowballStemmer('spanish') # stemmer en castellano
        self.show_all = False # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()
        self.use_multifield = False # 
        self.use_permuterm = False 
        self.numDoc = 0 # Contador del documento
        self.totalNoticias = 0
        self.totalIdNoticias = []
        self.indexID = {}
        

    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################


    def set_showall(self, v):
        """

        Cambia el modo de mostrar los resultados.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v


    def set_snippet(self, v):
        """

        Cambia el modo de mostrar snippet.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v


    def set_stemming(self, v):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v


    def set_ranking(self, v):
        """

        Cambia el modo de ranking por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON RANKING DE NOTICIAS

        si self.use_ranking es True las consultas se mostraran ordenadas, no aplicable a la opcion -C

        """
        self.use_ranking = v

    def set_multifield(self, v):

        self.use_multifield = v

    def set_permuterm(self, v):

        self.use_permuterm = v



    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################


    def index_dir(self, root, **args):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Recorre recursivamente el directorio "root"  y indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """

        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        self.set_permuterm(self.permuterm)
        self.set_multifield(self.multifield)

        for dir, subdirs, files in os.walk(root):
            for filename in files:
                if filename.endswith('.json'):
                    fullname = os.path.join(dir, filename)
                    self.index_file(fullname)
                    self.docs[self.numDoc] = fullname
                    self.numDoc = self.numDoc + 1
        #print(self.index)
        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################
        self.set_stemming(self.stemming)
        if self.use_stemming:
            self.make_stemming()
        if self.use_permuterm:
            self.make_permuterm()

        for new in self.termFreq.keys():
            for field in self.termFreq[new].keys():
                for token in self.termFreq[new][field].keys():
                    
                    term = (1 + math.log(self.termFreq[new][field][token]))
                    #print(field)
                    index = math.log(self.totalNoticias/len(self.index[field][token]))
                    self.termFreq[new][field][token] = (1 + math.log(self.termFreq[new][field][token])) * \
                                                        math.log(self.totalNoticias/len(self.index[field][token]))

            
        


        

    def index_file(self, filename):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Indexa el contenido de un fichero.

        Para tokenizar la noticia se debe llamar a "self.tokenize"

        Dependiendo del valor de "self.multifield" y "self.positional" se debe ampliar el indexado.
        En estos casos, se recomienda crear nuevos metodos para hacer mas sencilla la implementacion

        input: "filename" es el nombre de un fichero en formato JSON Arrays (https://www.w3schools.com/js/js_json_arrays.asp).
                Una vez parseado con json.load tendremos una lista de diccionarios, cada diccionario se corresponde a una noticia

        """

        with open(filename) as fh:
            jlist = json.load(fh)
        #COMPLETAR: ASIGNAR IDENTIFICADOR AL FICHER 'filename'
        numNoticia = 0
        for new in jlist:

            self.termFreq[self.totalNoticias] = {
                'article': {},
                'title': {},
                'summary': {},
                'keywords': {},
                'date': {}
            }
            #idNoticia = str(self.numDoc) +'.'+ str(numNoticia)
            #self.indexID[idNoticia] = self.totalNoticias
            self.news[self.totalNoticias]=[self.numDoc, numNoticia]
            #self.totalIdNoticias = self.totalIdNoticias + [idNoticia]
            
            # COMPLETAR: asignar identificador a la noticia 'new'
            content = new['article']
            title1 = new['title']
            summary1 = new['summary']
            keywords1 = new['keywords']
            date1 = new['date']
            # COMPLETAR: indexar el contenido 'content'
            #-------------------------------------ARTICLE------------------------------------------
            tokens = self.tokenize(content)
            for token in tokens:
                tokensIndex = (self.index['article'].get(token, []))

                self.termFreq[self.totalNoticias]['article'][token] = self.termFreq[self.totalNoticias]['article'].get(token,0) + 1
               
                if len(tokensIndex) == 0:
                    self.index['article'][token] = tokensIndex + [self.totalNoticias]
                else:    
                    ultim = tokensIndex[len(tokensIndex)-1]
                    
                    if ultim != self.totalNoticias:
                        self.index['article'][token] = tokensIndex + [self.totalNoticias]

            if self.use_multifield:
                #-------------------------------------TITLE------------------------------------------
                tokens = self.tokenize(title1)
                for token in tokens:

                    self.termFreq[self.totalNoticias]['title'][token] = self.termFreq[self.totalNoticias]['title'].get(token,0) + 1

                    tokensIndex = (self.index['title'].get(token, []))
                    if len(tokensIndex) == 0:
                        self.index['title'][token] = tokensIndex + [self.totalNoticias]
                    else:    
                        ultim = tokensIndex[len(tokensIndex)-1]
                        
                        if ultim != self.totalNoticias:
                            self.index['title'][token] = tokensIndex + [self.totalNoticias]

                #-------------------------------------SUMMARY-------------------------------------------
                tokens = self.tokenize(summary1)
                for token in tokens:

                    self.termFreq[self.totalNoticias]['summary'][token] = self.termFreq[self.totalNoticias]['summary'].get(token,0) + 1

                    tokensIndex = (self.index['summary'].get(token, []))
                    if len(tokensIndex) == 0:
                        self.index['summary'][token] = tokensIndex + [self.totalNoticias]
                    else:    
                        ultim = tokensIndex[len(tokensIndex)-1]
                        
                        if ultim != self.totalNoticias:
                            self.index['summary'][token] = tokensIndex + [self.totalNoticias]

                #-------------------------------------KEYWORDS-------------------------------------------
                tokens = self.tokenize(keywords1)
                for token in tokens:

                    self.termFreq[self.totalNoticias]['keywords'][token] = self.termFreq[self.totalNoticias]['keywords'].get(token,0) + 1

                    tokensIndex = (self.index['keywords'].get(token, []))
                    if len(tokensIndex) == 0:
                        self.index['keywords'][token] = tokensIndex + [self.totalNoticias]
                    else:    
                        ultim = tokensIndex[len(tokensIndex)-1]
                        
                        if ultim != self.totalNoticias:
                            self.index['keywords'][token] = tokensIndex + [self.totalNoticias]

                #-------------------------------------DATE-------------------------------------------
                tokensIndex = (self.index['date'].get(date1, []))

                self.termFreq[self.totalNoticias]['date'][date1] = self.termFreq[self.totalNoticias]['date'].get(date1,0) + 1

                if len(tokensIndex) == 0:
                    self.index['date'][date1] = tokensIndex + [self.totalNoticias]
                else:    
                    ultim = tokensIndex[len(tokensIndex)-1]
                        
                    if ultim != self.totalNoticias:
                        self.index['date'][date1] = tokensIndex + [self.totalNoticias]
            numNoticia = numNoticia + 1
            self.totalNoticias = self.totalNoticias + 1

            #hmmm
        


        #hahahaha
        # "jlist" es una lista con tantos elementos como noticias hay en el fichero,
        # cada noticia es un diccionario con los campos:
        #      "title", "date", "keywords", "article", "summary"
        #
        # En la version basica solo se debe indexar el contenido "article"
     



    def tokenize(self, text):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens
        """

        return self.tokenizer.sub(' ', text.lower()).split()



    def make_stemming(self):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING.

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        self.stemmer.stem(token) devuelve el stem del token

        """
        
        for token in self.index['article'].keys():
            stem = self.stemmer.stem(token)
            if self.sindex['article'].get(stem) is not None:
                self.sindex['article'][stem] = sorted(list(set(self.sindex['article'][stem] + self.index['article'][token])))
            else:
                self.sindex['article'][stem] = self.index['article'][token]
        if self.use_multifield:
            #-------------------------------------TITLE---------------------------------------------
            for token in self.index['title'].keys():
                stem = self.stemmer.stem(token)
                if self.sindex['title'].get(stem) is not None:
                    self.sindex['title'][stem] = sorted(list(set(self.sindex['title'][stem] + self.index['title'][token])))
                else:
                    self.sindex['title'][stem] = self.index['title'][token]
            #-------------------------------------SUMMARY---------------------------------------------
            for token in self.index['summary'].keys():
                stem = self.stemmer.stem(token)
                if self.sindex['summary'].get(stem) is not None:
                    self.sindex['summary'][stem] = sorted(list(set(self.sindex['summary'][stem] + self.index['summary'][token])))
                else:
                    self.sindex['summary'][stem] = self.index['summary'][token]

            #-------------------------------------KEYWORDS---------------------------------------------
            for token in self.index['keywords'].keys():
                stem = self.stemmer.stem(token)
                if self.sindex['keywords'].get(stem) is not None:
                    self.sindex['keywords'][stem] = sorted(list(set(self.sindex['keywords'][stem] + self.index['keywords'][token])))
                else:
                    self.sindex['keywords'][stem] = self.index['keywords'][token]
            
            #-------------------------------------DATE---------------------------------------------
            for token in self.index['date'].keys():
                stem = self.stemmer.stem(token)
                if self.sindex['date'].get(stem) is not None:
                    self.sindex['date'][stem] = sorted(list(set(self.sindex['date'][stem] + self.index['date'][token])))
                else:
                    self.sindex['date'][stem] = self.index['date'][token]
            

            
        #print(self.sindex.keys())
        pass
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################


    
    def make_permuterm(self):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        """
        #per cada token, agafem totes les permutacions
        #clavem cada permutacio en una llista
        #pa cada permutacio, tenim la paraula real que es
        #ordenem ixa llista
        #quan ens fan una consulta incompleta, ordenem de manera que es quede el asterisc al final a$b*
        #despres, fem una cerca dicotoimica de les permutacions que comencen per a$b, i per cada permutacio es guardem la paraula real
        #per a la consulta a*b, enjuntem les noticies de totes ixes paraules reals
        #
        #--------------------------------------------------------------------------------------------------
        #
        #--------------------------------------------------------------------------------------------------
        
        totalTraduccio = 0
        totalGetPermuterms = 0  
        totalIndex = 0  
        totalGet = 0
        totalAppend = 0
        for field in self.index.keys():
            
            t0 = time.time()
            for key in self.index[field].keys():
                
                t2 = time.time()
                permuterms = self.getPermuterms(key)
                t3 = time.time()
                totalGetPermuterms = totalGetPermuterms + (t3-t2)
                
                self.permFieldCount[field] = self.permFieldCount[field] + len(permuterms)
                
                for pterm in permuterms:
                    #self.pterms = self.pterms + [pterm]

                    t4 = time.time()
                    self.permToToken[pterm] = key
                    t5 = time.time()
                    totalTraduccio = totalTraduccio + (t5-t4)
                    prefix = pterm[0:2]

                    t6 = time.time()
                    l = self.ptindex.setdefault(prefix, [])
                    l.append(pterm)
                    t7 = time.time()
                    totalIndex = totalIndex + (t7-t6)

                    #totalIndexar = totalIndexar + (t7-t6)
            t1 = time.time()

            print(field + "Time making permuterm: %2.2fs." % (t1 - t0))
            print()
        print("permuterm: " + str(totalGetPermuterms))
        print("traduccio: " + str(totalTraduccio))
        print("indexar: " + str(totalIndex))
        # print("get: "+str(totalGet))
        # print("append: " + str(totalAppend))
        print(str(len(self.ptindex.keys())))

        # self.pterms = set(self.pterms)
        # print("-----------------------------longitud llista pterms--------------------------------------")
        # print(str(len(self.pterms)))

        # totalHash = 0
        # for key in self.ptindex.keys():
        #     self.ptindex[key] = sorted(self.ptindex[key])
        #     totalHash = totalHash + len(self.ptindex[key])
        
        # print("---------------------------longitud total del hash de pterms---------------------------- ")
        # print(str(totalHash))
        
        pass
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################


    def getPermuterms(self, word):
        i = 0
        term = '$'+word  
        permuterms = [term]
        while i < len(word):
            pre = word[0:i+1]
            suf =  word[i+1:len(word)] + '$'
            permuterms = permuterms + [suf + pre]
            i = i + 1
        return permuterms
        # i = 0
        # term = '$' + word
        # permuterms = [term]
        # while i < len(word):
        #     pre = word[0:i+1]
        #     suf = '$' + word[i+1:len(word)]
        #     permuterms = permuterms + [pre+suf]
        #     i = i + 1
        # return permuterms

        

    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        print("=====================================================")
        print("Number of indexed days: "+str(self.numDoc))
        print("-----------------------------------------------------")
        print("Number of indexed news: "+str(self.totalNoticias))
        print("-----------------------------------------------------")
        print("TOKENS:")
        print("\'article\': "+str(len(self.index['article'].keys())))
        if self.use_multifield:
            print("\'title\': "+str(len(self.index['title'].keys())))
            print("\'date\': "+str(len(self.index['date'].keys())))    
            print("\'keywords\': "+str(len(self.index['keywords'].keys())))
            print("\'summary\': "+str(len(self.index['summary'].keys())))
        print("-----------------------------------------------------")
        
        if self.use_stemming:
            print("STEMS: ")
            print("\'article\': "+str(len(self.sindex['article'].keys())))
            if self.use_multifield:
                print("\'title\': "+str(len(self.sindex['title'].keys())))
                print("\'date\': "+str(len(self.sindex['date'].keys())))    
                print("\'keywords\': "+str(len(self.sindex['keywords'].keys())))
                print("\'summary\': "+str(len(self.sindex['summary'].keys())))
            print("-----------------------------------------------------")

        if self.use_permuterm:
            print("PERMUTERM: ")
            print("\'article\': "+str(self.permFieldCount['article']))
            if self.use_multifield:
                print("\'title\': "+str(self.permFieldCount['title']))
                print("\'date\': "+str(self.permFieldCount['date']))
                print("\'keywords\': "+str(self.permFieldCount['keywords']))
                print("\'summary\': "+str(self.permFieldCount['summary']))
            print("-----------------------------------------------------")
            


        
        
        print("Positional queries are NOT allowed.")
        print("=====================================================")
        pass
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

        








    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################


    def solve_query(self, query, prev={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """

        if query is None or len(query) == 0:
            return []
        noticies = []
        postingListToken = []
        queryTokens=query.split()
        a=False
        n=False
        o=False
        for token in queryTokens:
            if token == 'NOT':
                n = True
            elif token == 'AND':
                a = True
            elif token == 'OR':
                o = True
            else:
                token = token.lower().split(':')
                # print(token)
                if len(token) == 1:
                    field = 'article'
                    token = token[0]
                else:
                    field = token[0]
                    token = token[1]
                # print(field)
                # print(token)


                if self.use_stemming:

                    if self.use_permuterm:
                        if '?' not in token and '*' not in token:
                            postingListToken = self.get_stemming(token, field)
                        else:
                            tokens = list(set(self.get_permuterm(token)))
                            #print(str(len(tokens)))
                            postingListToken = []
                            for token in tokens:
                                postingListToken = postingListToken + self.get_posting(token, field)
                            postingListToken = sorted(list(set(postingListToken)))
                    else:
                        postingListToken = self.get_stemming(token,field)

                else:

                    if self.use_permuterm:
                        tokens = list(set(self.get_permuterm(token)))
                        #print(str(len(tokens)))
                        postingListToken = []
                        for token in tokens:
                            postingListToken = postingListToken + self.get_posting(token, field)
                        #print(postingListToken)
                        postingListToken = sorted(list(set(postingListToken)))
                    else:
                        postingListToken = self.get_posting(token, field)

                #print(postingListToken)
                if n:
                    postingListToken = self.reverse_posting(postingListToken)
                    n = False
                if a:    
                    postingListToken = self.and_posting(noticies, postingListToken)
                    a = False
                if o:
                    postingListToken = self.or_posting(noticies, postingListToken)
                    o = False
                noticies = postingListToken
   
        #print(len(noticies))
        return noticies
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

 


    def get_posting(self, term, field):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve la posting list asociada a un termino. 
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """

        return self.index[field].get(term, [])
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def get_positionals(self, terms, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        pass
        ########################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE POSICIONALES ##
        ########################################################


    def get_stemming(self, term, field):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING

        Devuelve la posting list asociada al stem de un termino.

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """

        stem = self.stemmer.stem(term)
        return self.sindex[field].get(stem, [])
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################


    def get_permuterm(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        if '*' in term:
            tokens = []
            pterm = term.split('*')

            permuterm = pterm[1] + '$' + pterm[0]
            
            permuterms = self.ptindex[permuterm[0:2]]
            i = 0
            #print(permuterms[i] <= permuterm)
            #print('bbbbbbbbbbb'+str(len(permuterms)))
            while i < len(permuterms):
                #print(permuterms[i].startswith(permuterm))
                #print(permuterms[i]+'  '+permuterm)
                if permuterms[i].startswith(permuterm):
                #if permuterm in permuterms[i]:
                    tokens = tokens + [self.permToToken[permuterms[i]]]
                    
                i = i + 1
            return list(set(tokens))

        elif '?' in term:
            tokens = []
            pterm = term.split('?')

            permuterm = pterm[1] + '$' + pterm[0]
            
            permuterms = self.ptindex[permuterm[0:2]]
            i = 0
            #print(permuterms[i] <= permuterm)
            #print('bbbbbbbbbbb'+str(len(permuterms)))
            while i < len(permuterms):
                #print(permuterms[i].startswith(permuterm))
                #print(permuterms[i]+'  '+permuterm)
                if len(permuterms[i]) == (len(permuterm) + 1) and permuterms[i].startswith(permuterm):
                #if permuterm in permuterms[i]:
                    tokens = tokens + [self.permToToken[permuterms[i]]]
                    
                i = i + 1
            return list(set(tokens))

        else:
            #returm self.get_posting(term, field)
            return [term]
        
        ##################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA PERMUTERM ##
        ##################################################




    def reverse_posting(self, p):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los newid exceptos los contenidos en p

        """
        total = []
        i = 0
        j = 0
        #print(len(self.totalIdNoticias))
        while i < len(self.news.keys()) and j < len(p):
            
            if i == p[j]:
                j = j + 1
            else:
                total = total + [i]
            i = i + 1
        while i < len(self.news.keys()):
            total = total + [i]
            i = i + 1
        return total
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def and_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos en p1 y p2

        """
        total = []
        i = 0
        j = 0
        salt = 5

        while i < len(p1) and j < len(p2):
            if  (p1[i]) == (p2[j]):
                total = total + [p1[i]]
                i = i + 1
                j = j + 1
            elif  (p1[i] <  p2[j]):
                if i+salt < len(p1) and  (p1[i+salt]) <=  (p2[j]):
                    while i+salt < len(p1) and  (p1[i+salt]) <=  (p2[j]):
                        i = i + salt
                else:
                    i = i + 1
            else:
                if j+salt < len(p2) and  (p1[i]) >=  (p2[j + salt]):
                    while j+salt < len(p2) and  (p1[i]) >=  (p2[j+salt]):
                        j = j + salt
                else:
                    j = j + 1
                
        return total
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def or_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 o p2

        """
        total = []
        i = 0
        j = 0

        while i < len(p1) and j < len(p2):
            # print(p1[i])
            # print(p2[j])
            # print("----------")
            if  (p1[i]) ==  (p2[j]):
                total = total + [p1[i]]
                i = i + 1
                j = j + 1
            elif  (p1[i]) <  (p2[j]):
                total = total + [p1[i]]
                i = i + 1
               
            else:
                total = total + [p2[j]]
                j = j + 1
        while i < len(p1):
            total = total + [p1[i]]
            i = i + 1
        while j < len(p2):
            total = total + [p2[j]]
            j = j + 1

                
        return total
        
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################


    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se propone por si os es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 y no en p2

        """

        
        pass
        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################

    # def idToindex(self, l):
    #     indices = []
    #     for item in l:
    #         indices = indices + [self.indexID[item]]
    #     return indices

    # def indexToID(self, l):
    #     IDs = []
    #     for item in l:
    #         IDs = IDs + [self.totalIdNoticias[item]]
    #     return IDs




    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################


    def solve_and_count(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados 

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print("%s\t%d" % (query, len(result)))
        return len(result)  # para verificar los resultados (op: -T)


    def solve_and_show(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra informacion de las noticias recuperadas.
        Consideraciones:

        - En funcion del valor de "self.show_snippet" se mostrara una informacion u otra.
        - Si se implementa la opcion de ranking y en funcion del valor de self.use_ranking debera llamar a self.rank_result

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T
        
        """
        result = self.solve_query(query)
        if not self.show_all:
            result = result[0:99]

        if self.use_ranking:

            resultat = self.rank_result(result, query)
            result = resultat[0]
            pesos =  resultat[1]
        
        #print(result)
        print("=====================================================")
        print('Query: '+ query)
        print('Number of results: ' + str(len(result)))
        nNoticia = 1

        score = 0
        kk = 0
        for new in result:

            if self.use_ranking:
                score = pesos[kk]
                kk = kk + 1
            doc = self.news[new][0]
            path = self.docs[doc]
            pos = self.news[new][1]

            with open(path) as fh:
                jlist = json.load(fh)
            
            title = jlist[pos]['title']
            keyWords = jlist[pos]['keywords']
            date = jlist[pos]['date']
            content = jlist[pos]['article']

            if self.show_snippet:
                print('#'+str(nNoticia))
                print('Score: '+str(score))
                print(str(new))
                print('Date: '+date)
                print('Title: '+title)
                print('Keywords: '+keyWords)
                
                #queryTokens=self.tokenizer.sub(' ', query)
                queryTokens=self.elimina.sub(' ', query).split()
                #print(queryTokens)
                queryWords = []
                no = False
                for word in queryTokens:
                    if word == 'NOT':
                        no = True
                    else:
                        if not no:
                            queryWords = queryWords + [word]
                        else:
                            no = False

                #si apareix un not, eliminem el seguent token a NOT i aixi no ens apareix en cap consulta
                #si estem usant stemmings, s'elimina ixe stem. Per exemple, si en la query esta NOT doctor, tampoc es buscara doctora, doctors,etc.

                docTokens = self.tokenize(content)

                #traure llista de stemmings del content
                #la usem en paralel a la llista de tokens
                #comparem els tokens stemmizats, obtenim la posicio on coincidixen
                #a partir de ixa posicio, traguem el rang de tokens en la llista original
                docStems = []
                if self.use_stemming:
                    for token in docTokens:
                        docStems = docStems + [self.stemmer.stem(token)]
                #Si es not isla, el snipet no tornara res, perque son les noticies que no
                #tinguen isla, i en ixes noticies anem a buscar isla
                snipets=[]

                for w in queryWords:
                    w = w.lower().split(':')
                    if len(w) == 1:
                        w = w[0]
                        if '?' in w or '*' in w:
                            queryWords = queryWords + self.get_permuterm(w, 'article')
                    else:
                        w = w[1]
                        if '?' in w or '*' in w:
                            queryWords = queryWords + self.get_permuterm(w, w[0])
                            

                for w in queryWords:
                    try:
                        if self.use_stemming:
                            stem = self.stemmer.stem(w)
                            wIndex = docStems.index(stem)
                        else:
                            
                            wIndex = docTokens.index(w)
                        inici=max(0,wIndex-5)
                        fi=min(len(docTokens),wIndex+5)
                        snipets = snipets + [" ".join(docTokens[inici:fi])]
                    except ValueError:
                        pass
                    

                for snipet in snipets:
                    
                    print(snipet + ' ... ', end='')
                
                print('')
                if not nNoticia == len(result):
                    print("=====================================================")
            else:
                print('#'+str(nNoticia) + '\t' + '('+str(score)+')'+ ' ('+ str(new)+') (' + date+') '+ title + ' ('+keyWords+')')
                if not nNoticia == len(result):
                    print("--------------")

            nNoticia = nNoticia + 1
                
        print("=====================================================")        
    
                


                

            

            



            

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################





    def rank_result(self, result, query):
        """
        NECESARIO PARA LA AMPLIACION DE RANKING

        Ordena los resultados de una query.

        param:  "result": lista de resultados sin ordenar
                "query": query, puede ser la query original, la query procesada o una lista de terminos


        return: la lista de resultados ordenada

        """
        queryTokens=self.elimina.sub(' ', query).split()
        #print(queryTokens)
        queryWords = []
        no = False
        for word in queryTokens:
            if word == 'NOT':
                no = True
            else:
                if not no:
                    queryWords = queryWords + [word]
                else:
                    no = False

        newsScore = {}

        for w in queryWords:
            w = w.lower().split(':')
            if len(w) == 1:
                w = w[0]
                if '?' in w or '*' in w:
                    for permToken in self.get_permuterm(w, 'article'):
                        for new in result:
                            newsScore[new] = newsScore.get(permToken, 0) + self.termFreq[new]['article'].get(permToken, 0)
                else:
                    for new in result:
                        newsScore[new] = newsScore.get(w, 0) + self.termFreq[new]['article'].get(w, 0)


            else:
                word = w[1]
                if '?' in word or '*' in word:
                    for permToken in self.get_permuterm(word, w[0]):
                        for new in result:
                            newsScore[new] = newsScore.get(permToken, 0) + self.termFreq[new][w[0]].get(permToken, 0)
                else:
                    for new in result:
                        newsScore[new] = newsScore.get(word, 0) + self.termFreq[new][w[0]].get(word, 0)

        #newScoreOrdenat = list(dict.values())

        
        sortedDict = sorted(newsScore.items(), key=operator.itemgetter(1))

        resultatsOrdenats = [sortedDict[len(sortedDict)-1][0]]
        pesosOrdenats = [sortedDict[len(sortedDict)-1][1]]
        
        i = len(sortedDict) - 2
        while i >= 0:
            resultatsOrdenats.append(sortedDict[i][0])
            pesosOrdenats.append(sortedDict[i][1])

            i = i - 1

        return [resultatsOrdenats,pesosOrdenats]
            
        






        

        
        
        
        



        return []
        
        ###################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE RANKING ##
        ###################################################
