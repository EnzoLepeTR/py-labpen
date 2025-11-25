import oracledb
import requests
import logging, sys
import re
from datetime import datetime
import pyodbc

from clases.utils import Utils
from clases.utilsia import UtilsIA
from clases.configuracion import Configuracion
from clases.sumario import Sumario


class Fallo(Configuracion):

    def __init__(self):
        self.id = ""
        self.guid = ""
        self.titulo = ""
        self.tribunal = ""
        self.rol = ""
        self.fecha = ""
        self.partes = ""
        self.parteActiva = ""
        self.partePasiva = ""
        self.numeroCaracteres = 0
        self.archivo = ""
        self.documentid = ""
        self.texto = ""
        self.registrado = False
        self.linkOrigen = ""
        self.tag = ""
        self.tipoRecurso = ""
        self.tipoRecurso = ""
        self.hecho = ""
        self.collections = ['CL', 'CLLP', 'LYS', 'CLJG', 'CLPB', 'WLCLPREM', 'WLCLMED', 'WLCLINI']
        self.voces = list()
        self.data = self.getConfig()

    '''
       Método que determina si el fallo esta registrado en la base de datos de LOES
       '''

    def exist(self):

        i = 0
        cs = self.data["PJCS"]
        query = f"""Select id_fallo
                       from fallojuris3  
                       where datediff(dd,falFecha,'{self.fecha}')=0 and
    	                     falTribunal1 = '{self.tribunal}' and 
    	                     falrol = '{self.rol}'; """

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                i += 1
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        if (i != 0):
            return True
        else:
            return False

    '''
    '''
    def save(self):
        if self.texto.strip() == "":
            print(f"El fallo rol: { self.rol }, no ha podido ser grabado su sentencia es vacia", Exception())
            return False

        query = ""
        query = f"""INSERT INTO FalloJuris3 (
              fal_IdUltEdic
             ,fal_IdPenEdic
             ,falFUltEdic
             ,falFPenEdic
             ,falEdiciones
             ,falTribunal1
             ,falRol
             ,falSujA
             ,falSujP
             ,falArea
             ,falDescriptores
             ,falSentencia
             ,FalFecha
             ,FalPublicar
             ,FalAnalista
             ,FalTerminado
             ,falFechaCarga
             ,falSentencia2
             ,falTribunalBase
             ,FalRol2
             ,FalFecha2
             ,Falorigen
             ,FalLab
             ,Fal_TriLaPrimera
             ,FalRanking
             ,FalApelacion
             ,EsMasivo
             ,LinkOrigen
             ,NumeroCaracteres
           ) VALUES (
              1
             ,1
             ,getdate()
             ,getdate()
             ,0
             ,'{self.tribunal}'
             ,'{self.rol}'
             ,'{self.parteActiva}'
             ,'{self.partePasiva}'
             ,';1;'
             ,'{self.titulo}'
             ,'{self.texto.strip()}'
             ,'{self.fecha}'
             ,0
             ,0
             ,0
             ,getdate()
             ,'{self.texto.strip()}'
             ,0
             ,'{self.rol} '
             ,'{self.fecha}'
             ,'JOL'
             ,0
             ,0
             ,3
             ,'{self.tribunal}'
             ,2
             ,'{self.linkOrigen}'
             ,{self.numeroCaracteres}
           )"""

        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.execute("SELECT @@IDENTITY AS ID;")
            self.id = cursor.fetchone()[0]
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True


    '''
    '''
    def addVoces(self, voces):
        try:
            arrayVoces = voces.split(",")
            for voz in arrayVoces:
                self.voces.append(voz.strip())
        except:
            print("No se agregaran voces")

    '''
    '''

    def insertVoces(self, voz, idVoz):
        query = ""
        query = f"""insert into SAEVozRelacionada(id_fallo, id_voz, descripcion, sugerida) values({self.id}, {idVoz},'{voz}', 1);"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor
            print("[i] Agregada voz: " + voz)

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    Método que extrae las voces relacionadas a un fallo
    '''

    def getVoces(self):

        voces = list()
        try:
            cs = self.data["PJCS"]
            query = f"""select sv.faceta
                    from FalloJuris3 as f, SAEVoces as SV, SAEVozRelacionada AS SVR
                    where f.Id_Fallo = {self.id} and 
                        f.Id_Fallo = SVR.id_fallo and
                        SVR.id_voz = SV.id and 
                        sv.id_padre>0  
                    order by sv.faceta asc"""

            conection = pyodbc.connect(cs)
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                voces.append(row[0])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos fallo 103", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return voces

    '''
    '''

    def setVocesByTag(self, arrVoces):

        strVoces = UtilsIA.getVocesFromArr(arrVoces)
        strVoces = strVoces.replace(",", "','")

        cs = self.data["PJCS"]
        voces = list()
        query = f"""select ss.faceta, ss.id
                    from SAEVoces ss
                    where ss.faceta in ('{strVoces}') AND
                    ss.id_padre = {UtilsIA.getFacetaByTag(self.tag)} and
                    ss.id not in (SELECT sr.id_voz FROM SAEVozRelacionada sr where sr.id_fallo = {self.id})"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                self.insertVoces(row[0], row[1])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 139", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

    '''
    '''

    def setVocesByTag(self, arrVoces):

        strVoces = UtilsIA.getVocesFromArr(arrVoces)
        strVoces = strVoces.replace(",", "','")

        cs = self.data["PJCS"]
        voces = list()
        query = f"""select ss.faceta, ss.id
                    from SAEVoces ss
                    where ss.faceta in ('{strVoces}') AND
                    ss.id_padre = {UtilsIA.getFacetaByTag(self.tag)} and
                    ss.id not in (SELECT sr.id_voz FROM SAEVozRelacionada sr where sr.id_fallo = {self.id})"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                self.insertVoces(row[0], row[1])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 173", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

    '''
    '''

    def setVoces(self, arrVoces):

        strVoces = UtilsIA.getVocesFromArr(arrVoces)
        strVoces = strVoces.replace(",", "','")

        cs = self.data["PJCS"]
        voces = list()
        query = f"""select ss.faceta, ss.id
                        from SAEVoces ss
                        where ss.faceta in ('{strVoces}') AND                        
                        ss.id not in (SELECT sr.id_voz FROM SAEVozRelacionada sr where sr.id_fallo = {self.id})"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                self.insertVoces(row[0], row[1])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 207", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

    '''
    Método que proporciona los fallos de un sumario
    '''

    def getSumarios(self, limit=0):

        cs = self.data["PJCS"]
        sumarios = list()

        query = f"""select id_Doc_Sumario, id_fallo, texto from FalloSumario as fs where fs.id_fallo = {self.id}"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                sumario = Sumario()
                sumario.id = row[0]
                sumario.id_fallo = row[1]
                sumario.texto = row[2]
                sumarios.append(sumario)
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 243", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return sumarios

    '''
    '''

    def getIdDOC(self):
        date = datetime.strptime(self.fecha, "%d/%m/%Y")
        sDate = str(date.strftime("%Y%m%d"))
        sTime = str(380)
        idDoc = "CL_JJ_FLL_" + sTime + "_" + sDate + "_" + str(self.id)
        return idDoc

    '''
    '''

    def getColecciones(self):
        return self.collections

    '''
    '''

    def addColecciones(self, collections):
        try:
            arrayCollections = collections.split(",")
            for colection in arrayCollections:

                if re.search(r'[a-zA-Z]', colection):
                    self.collections.append(colection.strip())

        except:
            print("No se agregaran collections")

    '''
    '''

    def getLegislacion(self):

        cs = self.data["PJCS"]
        leyes = []
        query = f"""select numero, TIPONORMA, articulo, emisor from lconguid as l, SAEFallos2LCON sl  where l.guid = sl.GUIDLCON and sl.IDFallo = '{self.id}'"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                leyes.append("norma : " + Utils.formatNorma(row))
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 301", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return leyes

    '''
    '''

    def getMinistros(self, field=0):

        cs = self.data["PJCS"]
        ministros = list()
        query = f"""select guid, fms.apellidoynombre
                    from FalMinistrosxFallos fmf, falMinistrosSAE fms 
                    where fmf.ID_Fallo = {self.id} and 
                    fmf.ID_Ministro = fms.id_ministro"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                ministros.append(row[field].strip())
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 333", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return ministros

    '''
    Mëtodo que proporciona el tipo recurso de SAE
    '''

    def getTipoRecurso(self, field=0):
        cs = self.data["PJCS"]
        idTipoRecurso = ""
        query = f"""Select ID, descripcion from SAETipodeRecurso where LPTIREC={self.tipoRecurso}"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                idTipoRecurso = row[field].strip()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 362", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return idTipoRecurso

    '''
    Método que proporciona el id del tipo de resultado de SAE
    '''

    def getTipoResultado(self, field):
        cs = self.data["PJCS"]
        idTipoResultado = ""
        query = f"""Select id, descripcion from SAETipoResultado where IDTIRESUL={self.tipoResultado}"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                idTipoResultado = row[field].strip()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 391", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return idTipoResultado

    '''
    Método que proporciona el id del tribunal en SAE
    '''

    def getTribunal(self, field=0):
        cs = self.data["PJCS"]
        idTribunal = ""
        query = f"""select id, descripcion from SAETribunales_Chile as SAETChile where SAETChile.LPTRIB = {self.tribunal}"""

        conection = pyodbc.connect(cs)

        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                idTribunal = row[field].strip()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 420", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return idTribunal

    '''
    Método que prepara texto para que puedan ser cargados en la consulta SQL
    '''

    def prepareTextoSentencia(self, text):
        return ""

    '''
    Método que convierte el formato de la fecha de dd-mm-yyyyy a formato sql server YYYY-mm-dd hh:mm:ss
    '''

    def sqlDateFormat(self):
        try:
            date = datetime.strptime(self.fecha, "%d-%m-%Y")
            return date.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as exEstado:
            print(exEstado)
            return ""

    '''
    Método que carga todos los campos necesarios de un Fallo
    '''

    def getAllWithOutTitle(self, arrayIds):
        cs = self.data["PJCS"]
        fallos = list()

        query = f"""SELECT 
                        Id_Fallo,
                        isnull(falTribunal1,'') as falTribunal1, 
                        falRol, 
                        convert(varchar(10),falFecha,103) falFecha, 
                        isnull(falPartes,'') as falPartes, 
                        falSujA, 
                        falSujP,  
                        isnull(falDescriptores,'') as falDescriptores, 
                        falSentencia,
                        isnull(falTipoRecurso,0) as falTipoRecurso,
                        isnull(falResultado,0) as falResultado,
                        isnull(FalHecho, '') as FalHecho,
                        isnull(tag, '') as tag,
                        NumeroCaracteres
                    FROM FalloJuris3 
                    WHERE id_fallo in ({Utils.getListFromArray(arrayIds)}) 
                    ORDER BY id_fallo desc;"""

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                fallo = Fallo()
                fallo.id = row[0]
                fallo.tribunal = row[1]
                fallo.rol = row[2].strip()
                fallo.fecha = row[3]
                fallo.partes = row[4].strip()
                fallo.parteActiva = row[5].strip()
                fallo.partePasiva = row[6].strip()
                fallo.titulo = row[7].strip()
                fallo.texto = row[8].strip()
                fallo.tipoRecurso = row[9]
                fallo.tipoResultado = row[10]
                fallo.hecho = row[11].strip()
                fallo.tag = row[12].strip()
                fallo.numeroCaracteres = row[13]
                fallos.append(fallo)
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 500", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return fallos

    '''
    Método que carga todos los campos necesarios de un Fallo
    '''

    def getAll(self, arrayIds):
        cs = self.data["PJCS"]
        fallos = list()
        query = f"""SELECT 
                        Id_Fallo,
                        isnull(falTribunal1,'') as falTribunal1, 
                        falRol, 
                        convert(varchar(10),falFecha,103) falFecha, 
                        isnull(falPartes,'') as falPartes, 
                        falSujA, 
                        falSujP,  
                        isnull(falDescriptores,'') as falDescriptores, 
                        falSentencia,
                        isnull(falTipoRecurso,0) as falTipoRecurso,
                        isnull(falResultado,0) as falResultado,
                        isnull(FalHecho, '') as FalHecho
                    FROM FalloJuris3 
                    WHERE id_fallo in ({Utils.getListFromArray(arrayIds)}) 
                    ORDER BY id_fallo desc;"""

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                fallo = Fallo()
                fallo.id = row[0]
                fallo.tribunal = row[1]
                fallo.rol = row[2].strip()
                fallo.fecha = row[3]
                fallo.partes = row[4].strip()
                fallo.parteActiva = row[5].strip()
                fallo.partePasiva = row[6].strip()
                fallo.titulo = row[7].strip()
                fallo.texto = row[8].strip()
                fallo.tipoRecurso = row[9]
                fallo.tipoResultado = row[10]
                fallo.hecho = row[11].strip()
                fallos.append(fallo)
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 556", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return fallos

    '''
    Método que carga todos los campos necesarios de un Fallo
    '''

    def load(self, id):
        cs = self.data["PJCS"]
        query = f"""SELECT 
                        Id_Fallo,
                        isnull(falTribunal1,'') as falTribunal1, 
                        falRol, 
                        convert(varchar(10),falFecha,103) falFecha, 
                        isnull(falPartes,'') as falPartes, 
                        falSujA, 
                        falSujP,  
                        isnull(falDescriptores,'') as falDescriptores, 
                        falSentencia,
                        isnull(falTipoRecurso,0) as falTipoRecurso,
                        isnull(falResultado,0) as falResultado,
                        isnull(FalHecho, '') as FalHecho,
                        jg.guid
                    FROM FalloJuris3, JOLGUID AS JG
                    WHERE id_fallo = {id} and 
                    convert(varchar,Id_Fallo, 10) = jg.CITA
                    ORDER BY id_fallo desc;"""

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                self.id = row[0]
                self.tribunal = row[1]
                self.rol = row[2].strip()
                self.fecha = row[3]
                self.partes = row[4].strip()
                self.parteActiva = row[5].strip()
                self.partePasiva = row[6].strip()
                self.titulo = row[7].strip()
                self.texto = row[8].strip()
                self.tipoRecurso = row[9]
                self.tipoResultado = row[10]
                self.hecho = row[11].strip()
                self.guid = row[12].strip()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 556", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    Método que carga todos los campos necesarios de un Fallo
    '''

    def getAllWithGUID(self, arrayIds):
        cs = self.data["PJCS"]
        fallos = list()
        query = f"""SELECT 
                            Id_Fallo,
                            isnull(falTribunal1,'') as falTribunal1, 
                            falRol, 
                            convert(varchar(10),falFecha,103) falFecha, 
                            isnull(falPartes,'') as falPartes, 
                            falSujA, 
                            falSujP,  
                            isnull(falDescriptores,'') as falDescriptores, 
                            falSentencia,
                            isnull(falTipoRecurso,0) as falTipoRecurso,
                            isnull(falResultado,0) as falResultado,
                            isnull(FalHecho, '') as FalHecho,
                            jg.guid
                        FROM FalloJuris3, JOLGUID AS JG
                        WHERE id_fallo in ({Utils.getListFromArray(arrayIds)}) and 
                            convert(varchar,Id_Fallo, 10) = jg.CITA
                        ORDER BY id_fallo desc;"""

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                fallo = Fallo()
                fallo.id = row[0]
                fallo.tribunal = row[1]
                fallo.rol = row[2].strip()
                fallo.fecha = row[3]
                fallo.partes = row[4].strip()
                fallo.parteActiva = row[5].strip()
                fallo.partePasiva = row[6].strip()
                fallo.titulo = row[7].strip()
                fallo.texto = row[8].strip()
                fallo.tipoRecurso = row[9]
                fallo.tipoResultado = row[10]
                fallo.hecho = row[11].strip()
                fallo.guid = row[12].strip()
                fallos.append(fallo)
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 616", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

        return fallos

    '''
    '''

    def updateTitulo(self):

        if self.titulo.strip() == "":
            print(f"El fallo rol: {self.rol}, no ha podido actualizado, titulo vacio", Exception())
            return False

        query = ""
        query = f"""update FalloJuris3 set falDescriptores = '{self.titulo}' where Id_Fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def updateTipoRecurso(self, intTipoRecurso):

        query = ""
        query = f"""update FalloJuris3 set falTipoRecurso = '{intTipoRecurso}' where Id_Fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def updateFalloTerminado(self):
        query = ""
        query = f"""update FalloJuris3 set falTerminado = 1 where Id_Fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def updateResultado(self, intResultado):

        query = ""
        query = f"""update FalloJuris3 set falResultado = '{intResultado}' where Id_Fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def delMinistros(self):

        query = ""
        query = f"""Delete from FalMinistrosxFallos Where Id_Fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    7352 SENTENCIA ORIGINAL
    '''

    def delVoz(self, idVoz):

        query = ""
        query = f"""DELETE FROM SAEVozRelacionada WHERE id_voz = {idVoz} AND id_fallo = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor
            print("[i] Voz eliminada ")

        except Exception as exEstado:
            print("[!] Error al grabar datos[Eliminar Voz] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def insertMinistro(self, idMinistro):

        query = ""
        query = f"""Insert Into FalMinistrosxFallos(ID_Fallo, ID_Ministro) values({self.id},{idMinistro});"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def setJolCita(self):
        query = ""
        query = f"""insert into jolguid(cita) values({self.id});"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] en jolguid ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def setJolGUID(self, cita, guid, documentoId, citaOnLine):
        query = ""
        query = f"""UPDATE jolguid SET guid='{guid}', documentoid={documentoId}, citaonline='{citaOnLine}' where cita='{cita}';"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[FALLO] en jolguid update", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    Metodo que proporciona una lista fallos que no poseen GUID
    '''

    def getJolGUIDList(self):

        cs = self.data["PJCS"]
        citas = list()
        query = f"""SELECT cita                            
                        FROM JOLGUID AS JG
                        WHERE guid is null
                        ORDER BY cita desc;"""

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                citas.append(row[0])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 616", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass
        return citas

    '''
    Método que consulta sobre los datos de un fallo, mediante su cita, en SAE
    '''

    def getJolGUID(self, cita):

        data_source = self.data.get("SAE", {}).get("DataSource")
        user = self.data.get("SAE", {}).get("User")
        password = self.data.get("SAE", {}).get("Pass")

        query = """
        SELECT
        D.GUID,
        D.DOCUMENTOID,
        REPLACE(CD.DESCRIPCION, '_CL', '') AS CITA,
        CDD.DESCRIPCION AS CITAONLINE
        FROM DOCUMENTO D
        JOIN DOCUMENTOJURISPRUDENCIA DJ ON D.DOCUMENTOID = DJ.DOCUMENTO
        JOIN CITA_DOCU CD ON CD.DOCUMENTOID = D.DOCUMENTOID
        JOIN CITA_DOCU CDD ON CDD.DOCUMENTOID = D.DOCUMENTOID
        WHERE
        D.TIPODOCUMENTO = 1
        AND D.PAIS_ID = '1adfa838-938d-28e3-8193-8d28e633d8b6'
        AND CD.VIGENTE = 0
        AND (CD.DESCRIPCION = :cita1 OR CD.DESCRIPCION = :cita2)
        AND CDD.VIGENTE = 1
        FETCH FIRST 1 ROWS ONLY
        """

        params = {
            "cita1": str(cita),
            "cita2": str(cita) + "_CL"
        }

        guid = ''
        documentoid = ''
        citaonline = ''

        with oracledb.connect(user=user, password=password, dsn=data_source) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                col_names = [d[0] for d in cur.description]
                for row in cur:
                    data = dict(zip(col_names, row))
                    guid = data["GUID"]
                    documentoid = data["DOCUMENTOID"]
                    citaonline = data["CITAONLINE"]

        return guid, documentoid, citaonline

    '''
    '''

    def updateHecho(self, intTipoRecurso, intResultado):

        falHecho = UtilsIA.getHecho(intTipoRecurso, intResultado)

        if falHecho == "":
            return

        query = ""
        query = f"""update FalloJuris3 set falhecho = '{falHecho}' where id_fallo = {self.id};"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar hecho [FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def delMasivo(self):

        query = ""
        query = f"""update FalloJuris3 set esmasivo = 0 where id_fallo = {self.id};"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al eliminar de masivo", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def getRelacionsLcon(self):
        cs = self.data["PJCS"]
        relaciones = list()
        query = f"exec RelacionesLcon @IdFallo = {self.id};"

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                relacion = {
                    "GUID ORIGEN": row[0],
                    "GUID DESTINO": row[1],
                    "TIPO": row[2],
                    "SUB TIPO IDA": row[3],
                    "SUB TIPO VUELTA": row[4],
                    "Comentario Ida": row[5],
                    "Comentario Vuelta": row[6],
                    "Estado": row[7],
                    "Errores": row[8]
                }

                relaciones.append(relacion)

            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 1053", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass
        return relaciones

    '''
    '''

    def getRelacionesLconTria(self):
        cs = self.data["PJCS"]
        relaciones = list()
        query = f"exec RelacionesLconTria @IdFallo = {self.id};"

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                relacion = {
                    "rol": row[0],
                    "fecha": row[1],
                    "tribunal": row[2],
                    "titulo": row[3],
                    "fallo": row[4],
                    "legislacion": row[5]
                }

                relaciones.append(relacion)

            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al extraer datos 1053", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass
        return relaciones

    '''
    Método que determina si el fallo ha sido analizado o no
    '''

    def existAnalist(self):

        voces = self.getVoces()

        # Verificar si el número 3 está en la lista
        if "ANALISIS.IA" in voces or "ANALISIS.DEL.EDITOR" in voces:
            return True
        else:
            return False

    def getRelacionsJols(self):

        umbral = 0.73
        relaciones = list();

        Url = self.data.get("Qdrant", {}).get("Url")
        CollectionName = self.data.get("Qdrant", {}).get("CollectionName")
        ApiKey = self.data.get("Qdrant", {}).get("ApiKey")

        try:
            url = f"{Url}/collections/{CollectionName}/points/recommend"

            payload = {
                "positive": [self.id],
                "negative": [],
                "limit": 15,
                "with_payload": True,
                "with_vector": False,
                "filter": {"must_not": [{"has_id": [self.id]}]},
                "strategy": "best_score"
            }

            headers = {
                "Content-Type": "application/json",
                "api-key": ApiKey
            }

            response = requests.request("POST", url, json=payload, headers=headers)

            if response.status_code == 200:
                results = response.json()
                if results.get("result"):
                    results = results.get("result")
                    for result in results:
                        if (result['score'] > umbral):
                            relacion = {
                                "GUID ORIGEN": self.guid,
                                "GUID DESTINO": result['payload']['guid'],
                                "TIPO": 'JR',
                                "SUB TIPO IDA": 'Jurisprudencia Relacionada',
                                "SUB TIPO VUELTA": 'Jurisprudencia Relacionada',
                                "Comentario Ida": '',
                                "Comentario Vuelta": '',
                                "Estado": '',
                                "Errores": ''
                            }
                            relaciones.append(relacion)


        except:
            print(f"❌ Error al llamar a Qdrant fallo 1161")

        return relaciones

    '''
    '''

    def update(self):

        query = f"""
            UPDATE FalloJuris3 SET
                 falFUltEdic = getdate()
                , falFPenEdic = getdate()
                , falEdiciones = falEdiciones + 1                
                , falDescriptores = '{self.titulo}'
                , Falhecho = '{self.getHecho()}'
                , faltipoRecurso = {self.tipoRecurso}
                , falResultado = {self.resultado}
            WHERE Id_Fallo = {self.id}
        """

        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al actualizar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def getHecho(self):

        if not self.hecho:
            return ""
        else:
            self.hecho = self.hecho.replace("'", '´')
            return self.hecho

    '''
    '''

    def delSumarios(self):

        query = f"""
            delete from FalloSumario where id_fallo = {self.id}
        """

        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al actualizar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def delVoces(self, vozId):
        query = f"""
            delete from SAEVozRelacionada where id_fallo = {self.id} and id_voz = {vozId}
        """

        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al actualizar datos[FALLO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    Mëtodo que graba las voces del fallo
    '''

    def saveVoces(self, id, voz):
        query = ""
        if id in [2783, 2641]:
            return True

        query = f"insert into SAEVozRelacionada(id_fallo, id_voz, descripcion, sugerida) values({self.id}, {id}, '{voz}', 1);"

        cs = self.data["PJCS"]
        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            print(f"La voz: {voz}, a sido agregada.")
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[VOCES] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    '''

    def saveLegislacion(self, lconguid, lconSugerida):
        query = ""

        query = f"insert into saefallos2lcon(IDFallo, GUIDLCON, fechacreacion, tag) values({self.id}, '{lconguid}', getdate(), '{lconSugerida}');"

        cs = self.data["PJCS"]
        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            print(f"La norma: {lconguid}, a sido agregada.")
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[LEGISLACION] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    '''
    Método que graba los sumarios de un fallo
    '''

    def saveSumario(self, sumario="Sin referencia"):
        query = ""
        sumario = sumario.replace("'", "´")
        query = f"insert into fallosumario(id_fallo, texto) values({self.id}, '{sumario}');"

        cs = self.data["PJCS"]
        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            print("El sumario ha sido agregado")
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[SUMARIO] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    def saveMinistro(self, id):
        query = ""

        query = f"insert into FalMinistrosxFallos(ID_Fallo, ID_Ministro) values({self.id}, {id});"

        cs = self.data["PJCS"]
        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            print(f"El ministro: {id}, a sido agregada.")
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[Ministros] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True