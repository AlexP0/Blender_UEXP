bl_info = {
    "name": "Uexp Editor",
    "author": "AlexPo",
    "location": "Properties > Scene Properties > Uexp Panel",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "description": "Creates a point cloud from uexp vertex data to allow modification, and writes the modified coordinates back in the uexp",
    "category": "Import-Export"
    }


import bpy
import bmesh

import os
import sys
import struct

from bpy_extras.io_utils import ImportHelper

#The code basically reads bytes by group of 4 to get floats. 
#3 floats read give us the x,y,z coordinates of a vertex. 
#We then create that vertex in a mesh, and repeat for all vertices.
#Once the mesh edited we do the opposite
#Get the float coordinates of a vertex and write it to the uexp as bytes.


def ClearProperties(self,context):
    UEXPEditor = bpy.context.scene.UEXPEditor
    UEXPEditor.LOD0vStart = 0
    UEXPEditor.LOD0vEnd = 0
    UEXPEditor.LOD1vStart = 0
    UEXPEditor.LOD1vEnd = 0
    UEXPEditor.LOD2vStart = 0
    UEXPEditor.LOD2vEnd = 0
    UEXPEditor.LOD3vStart = 0
    UEXPEditor.LOD3vEnd = 0
    return None

class UEXPSettings(bpy.types.PropertyGroup):
    UexpPath : bpy.props.StringProperty(subtype='FILE_PATH', update=ClearProperties)
    UexpSize : bpy.props.IntProperty()
    LOD0vStart: bpy.props.IntProperty()
    LOD0vEnd: bpy.props.IntProperty()
    LOD1vStart: bpy.props.IntProperty()
    LOD1vEnd: bpy.props.IntProperty()
    LOD2vStart: bpy.props.IntProperty()
    LOD2vEnd: bpy.props.IntProperty()
    LOD3vStart: bpy.props.IntProperty()
    LOD3vEnd : bpy.props.IntProperty()
    
    LOD0fStart: bpy.props.IntProperty()
    LOD0fEnd: bpy.props.IntProperty()
    LOD0fSize: bpy.props.IntProperty()
    LOD1fStart: bpy.props.IntProperty()
    LOD1fEnd: bpy.props.IntProperty()
    LOD1fSize: bpy.props.IntProperty()
    LOD2fStart: bpy.props.IntProperty()
    LOD2fEnd: bpy.props.IntProperty()
    LOD2fSize: bpy.props.IntProperty()
    LOD3fStart: bpy.props.IntProperty()
    LOD3fEnd : bpy.props.IntProperty()
    LOD3fSize : bpy.props.IntProperty()
    

#Read vertex data and face data from uexp and create mesh of it.
def CreateMesh(LOD):
    UEXPEditor = bpy.context.scene.UEXPEditor
    
    if LOD == 0:
        LODvStart = UEXPEditor.LOD0vStart
        LODvEnd = UEXPEditor.LOD0vEnd
        LODfStart = UEXPEditor.LOD0fStart
        LODfEnd = UEXPEditor.LOD0fEnd
        LODfSize = UEXPEditor.LOD0fSize
        LODsuffix="_LOD0"
    if LOD == 1:
        LODvStart = UEXPEditor.LOD1vStart
        LODvEnd = UEXPEditor.LOD1vEnd
        LODfStart = UEXPEditor.LOD1fStart
        LODfEnd = UEXPEditor.LOD1fEnd
        LODfSize = UEXPEditor.LOD1fSize
        LODsuffix="_LOD1"
    if LOD == 2:
        LODvStart = UEXPEditor.LOD2vStart
        LODvEnd = UEXPEditor.LOD2vEnd
        LODfStart = UEXPEditor.LOD2fStart
        LODfEnd = UEXPEditor.LOD2fEnd
        LODfSize = UEXPEditor.LOD2fSize
        LODsuffix="_LOD2"
    if LOD == 3:
        LODvStart = UEXPEditor.LOD3vStart
        LODvEnd = UEXPEditor.LOD3vEnd
        LODfStart = UEXPEditor.LOD3fStart
        LODfEnd = UEXPEditor.LOD3fEnd
        LODfSize = UEXPEditor.LOD3fSize
        LODsuffix="_LOD3"
    
    
    with open (UEXPEditor.UexpPath, 'rb') as f:
        #Read 4 bytes and unpack a float out of it for X, 
        #read the next 4 for Y and the next for Z
        def ReadVertex(rOffset):
            f.seek(rOffset)
            
            bData = f.read(4)
            x = struct.unpack('<f',bData)[0] 
            bData = f.read(4)
            y = struct.unpack('<f',bData)[0] 
            bData = f.read(4)
            z = struct.unpack('<f',bData)[0]        
            
            v = [x,y,z]
            return v

        vList = []
           
        #For each vertex we ask ReadVertex() to give us the coordinates.
        #We move by steps of 12 bytes (3 floats)
        for n in range(LODvStart,LODvEnd,12):   
            v = ReadVertex(n)
            #We add the vertex read to the vList
            vList.append(v)
        
    with open (UEXPEditor.UexpPath, 'rb') as f:         
        def ReadFace(rOffset):
            f.seek(rOffset)
            
            if LODfSize == 12:
                bData = f.read(4)
                v1 = struct.unpack('<i',bData)[0]
                bData = f.read(4)
                v2 = struct.unpack('<i',bData)[0]
                bData = f.read(4)
                v3 = struct.unpack('<i',bData)[0]
                face = [v1,v2,v3]
                return face
                
            if LODfSize == 6:
                bData = f.read(2)
                v1 = struct.unpack('<H',bData)[0]
                bData = f.read(2)
                v2 = struct.unpack('<H',bData)[0]
                bData = f.read(2)
                v3 = struct.unpack('<H',bData)[0]            
                face = [v1,v2,v3]            
                return face
        
        eList = [] #just a stand-in for edge data
        
        fList = []    
        
        for n in range (LODfStart,LODfEnd,LODfSize):
            nface = ReadFace(n)
            fList.append(nface)
    
    #Create vertex cloud
    def VCloud(object_name, vList, eList=[],fList=[]):
              
        #Create a mesh
        mesh = bpy.data.meshes.new(object_name+"Mesh")
        #Create an object with our created mesh assigned.
        object = bpy.data.objects.new(object_name, mesh)
              
        bm = bmesh.new()
    
        for face in fList:          
            v1i = face[0]        
            v1co = vList[v1i]
            v1 = bm.verts.new(v1co)

            v2i = face[1]
            v2co = vList[v2i]
            v2 = bm.verts.new(v2co)
            
            v3i = face[2]
            v3co = vList[v3i]
            v3 = bm.verts.new(v3co)

            f1 = [v1,v2,v3]
            bm.faces.new(f1)
                    
        bm.to_mesh(mesh)
        bm.free()
       
        object.show_name = True
       
        mesh.update()
        return object
    
    objectprefix = os.path.split(UEXPEditor.UexpPath)[1]
    objectprefix = objectprefix[:-5]
    
    vCloud = VCloud(objectprefix+LODsuffix, vList,eList,fList)
    
    #We add the created object to a collection
    bpy.context.collection.objects.link(vCloud)



#This is where we write the modified vertex data back into the uexp
def WriteMesh(LOD): 
    UEXPEditor = bpy.context.scene.UEXPEditor
    
    if LOD == 0:
        LODvStart = UEXPEditor.LOD0vStart
        LODvEnd = UEXPEditor.LOD0vEnd
        LODfStart = UEXPEditor.LOD0fStart
        LODfEnd = UEXPEditor.LOD0fEnd
        LODsuffix="_LOD0"
    if LOD == 1:
        LODvStart = UEXPEditor.LOD1vStart
        LODvEnd = UEXPEditor.LOD1vEnd
        LODfStart = UEXPEditor.LOD1fStart
        LODfEnd = UEXPEditor.LOD1fEnd
        LODsuffix="_LOD1"
    if LOD == 2:
        LODvStart = UEXPEditor.LOD2vStart
        LODvEnd = UEXPEditor.LOD2vEnd
        LODfStart = UEXPEditor.LOD2fStart
        LODfEnd = UEXPEditor.LOD2fEnd
        LODsuffix="_LOD2"
    if LOD == 3:
        LODvStart = UEXPEditor.LOD3vStart
        LODvEnd = UEXPEditor.LOD3vEnd
        LODfStart = UEXPEditor.LOD3fStart
        LODfEnd = UEXPEditor.LOD3fEnd
        LODsuffix="_LOD3"
    
    objectprefix = os.path.split(UEXPEditor.UexpPath)[1]
    objectprefix = objectprefix[:-5]
    objectname = objectprefix+LODsuffix
    #Gotta have the object as active selected for this to work
    EditedMesh = bpy.data.objects[objectname].data
    
    
    #Returns the binary coordinates of the given vertex index. 
    def GetVCoords(index):
        
        #get coordinates of vertex
        x = EditedMesh.vertices[index].co[0]
        y = EditedMesh.vertices[index].co[1]
        z = EditedMesh.vertices[index].co[2]
        
        #turn these float coordinates into bytes
        xb = struct.pack('<f',x)
        yb = struct.pack('<f',y)
        zb = struct.pack('<f',z)
        
        #binary vertex coordinates
        vb = [xb,yb,zb]
        
        #print (xb,yb,zb)
        return vb
    
    #Write the new binary vertex coordinates to the uexp
    def WriteVBin(vOffset,vBinCoords):
        f.seek(vOffset)
        for i in vBinCoords:
            f.write(i)
        
    with open (UEXPEditor.UexpPath, 'rb+') as f:
        vIndex = -1
        #For each vertex we get its coordinates and write them to uexp.
        for n in range(LODvStart, LODvEnd-12, 12):
            vIndex += 1
            vbCoords = GetVCoords(vIndex)
            WriteVBin(n,vbCoords)


#Finds start and end offsets of vertex data
def FindVertexOffsets(SearchOffset):
    UEXPEditor = bpy.context.scene.UEXPEditor
    UEXPEditor.UexpSize = os.path.getsize(UEXPEditor.UexpPath)
    
    startOffset = 0
    endOffset = 0
    
    #We go through the whole file byte by byte, 
    #reading 12 bytes trying to find 2 sets of interlocking int
    with open (UEXPEditor.UexpPath, 'rb') as f:
        for n in range(SearchOffset,UEXPEditor.UexpSize):            
            f.seek(n)
            int1 = f.read(4)
            intA = f.read(4)
            int2 = f.read(4)
            intB = f.read(4)
            
            if len(intA)==4:
                itemsize = struct.unpack('<i',int1)
                vertcount = struct.unpack('<i',intA)
                if itemsize[0] == 12 and vertcount[0] > 3:
                    if int1 == int2 and intA == intB:
                        vdatalength = itemsize[0]*vertcount[0]
                        if vdatalength < UEXPEditor.UexpSize-n:
                            f.seek(vdatalength,1)
                            offset = f.tell()
                            f.seek(6,1)
                            bdata = f.read(4)
                            if bdata == intA:
                                startOffset = n+16
                                endOffset = offset
                                break
            else:
                print("LOD not found")
                break
                
    print(startOffset, endOffset)            
    return startOffset, endOffset




#We want to find where face data starts and end in the uexp file
def FindFaceOffsets(vStart,vEnd):
    UEXPEditor = bpy.context.scene.UEXPEditor
    
    startOffset = 0
    endOffset = 0
    
    int02 = b'\x00\x00\x00\x02\x02\x00\x00\x00'
    int04 = b'\x00\x00\x00\x04\x04\x00\x00\x00'
    
    vCount = (vEnd - vStart)/12
    if vCount > 65535:
        byteSearch = int04
        itemSize = 4
    else:
        byteSearch = int02
        itemSize = 2  
    
    with open (UEXPEditor.UexpPath, 'rb') as f:
    
        for n in range(vStart,0,-1):
            f.seek(n)
            bData = f.read(8) 
            if bData == byteSearch:
                startOffset = n+12 #12 is to get past the 8 bytes we were search for and the next 4 which indicate vertex index count
                break
                
        if startOffset != 0:
            f.seek(startOffset-4)
            bindexCount = f.read(4)
            iCount = struct.unpack('<i',bindexCount)[0]
            fDataSize = iCount * itemSize
            endOffset = startOffset + fDataSize - (3*itemSize)
    
    itemSize = itemSize * 3
    return startOffset, endOffset, itemSize
        
        
def SearchLODOffsets(LOD=0):
    UEXPEditor = bpy.context.scene.UEXPEditor
    
    if LOD >= 0:
        UEXPEditor.LOD0vStart,UEXPEditor.LOD0vEnd = FindVertexOffsets(0)
        UEXPEditor.LOD0fStart,UEXPEditor.LOD0fEnd,UEXPEditor.LOD0fSize  = FindFaceOffsets(UEXPEditor.LOD0vStart,UEXPEditor.LOD0vEnd)
    if LOD >= 1:
        UEXPEditor.LOD1vStart,UEXPEditor.LOD1vEnd = FindVertexOffsets(UEXPEditor.LOD0vStart)
        UEXPEditor.LOD1fStart,UEXPEditor.LOD1fEnd,UEXPEditor.LOD1fSize = FindFaceOffsets(UEXPEditor.LOD1vStart,UEXPEditor.LOD1vEnd)
    if LOD >= 2:
        UEXPEditor.LOD2vStart,UEXPEditor.LOD2vEnd = FindVertexOffsets(UEXPEditor.LOD1vStart)
        UEXPEditor.LOD2fStart,UEXPEditor.LOD2fEnd,UEXPEditor.LOD2fSize = FindFaceOffsets(UEXPEditor.LOD2vStart,UEXPEditor.LOD2vEnd)
    if LOD >= 3:
        UEXPEditor.LOD3vStart,UEXPEditor.LOD3vEnd = FindVertexOffsets(UEXPEditor.LOD2vStart)
        UEXPEditor.LOD3fStart,UEXPEditor.LOD3fEnd,UEXPEditor.LOD3fSize = FindFaceOffsets(UEXPEditor.LOD3vStart,UEXPEditor.LOD3vEnd)
    
    return {'FINISHED'}




##### PANEL UI STUFF #######


class ImportUexp(bpy.types.Operator):
    """Creates a mesh from vertex data"""
    bl_idname = "object.import_uexp"
    bl_label = "Import"
    
    LODtoLoad: bpy.props.IntProperty(
        name = 'LOD',
        default = 0
        )
    
    def execute(self, context):
        
        CreateMesh(self.LODtoLoad)
        return {'FINISHED'}

    
class ExportUexp(bpy.types.Operator):
    """Writes the modified vertex positions backs into the uexp"""
    bl_idname = "object.export_uexp"
    bl_label = "Export"

    LODtoWrite: bpy.props.IntProperty(
        name = 'LOD',
        default = 0
        )
        
    def execute(self, context):
        WriteMesh(self.LODtoWrite)
        return {'FINISHED'}

class SearchForOffsets(bpy.types.Operator):
    """Searches the uexp for the begin and end offsets of vertex data"""
    bl_idname = "object.search_offsets"
    bl_label = "Search Vertex Offset"
    
    
       
    def execute(self, context):
        SearchLODOffsets(2)
        
        return{'FINISHED'}
    

class UexpPanel(bpy.types.Panel):
    """Creates a Panel in the Scene properties window"""
    bl_label = "Uexp Panel"
    bl_idname = "OBJECT_PT_uexp"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        UEXPEditor = context.scene.UEXPEditor
        
        row = layout.row()
        row.prop(UEXPEditor,'UexpPath')
            
        row = layout.row()
        row.operator("object.search_offsets", icon='ZOOM_ALL')
        
        row = layout.row()
        if UEXPEditor.LOD0vStart != 0:
            row.label(text="LOD0: "+str(UEXPEditor.LOD0vStart)+" - "+str(UEXPEditor.LOD0vEnd), icon='MESH_ICOSPHERE')
            LOD0Button = row.operator("object.import_uexp", icon='MESH_ICOSPHERE')
            LOD0Button.LODtoLoad = 0
            LOD0ButtonE = row.operator("object.export_uexp", icon='SCRIPTPLUGINS')
            LOD0ButtonE.LODtoWrite = 0
        
        row = layout.row()
        if UEXPEditor.LOD1vStart != 0:
            row.label(text="LOD1: "+str(UEXPEditor.LOD1vStart)+" - "+str(UEXPEditor.LOD1vEnd), icon='MESH_ICOSPHERE')
            LOD1Button = row.operator("object.import_uexp", icon='MESH_ICOSPHERE')
            LOD1Button.LODtoLoad = 1
            LOD1ButtonE = row.operator("object.export_uexp", icon='SCRIPTPLUGINS')
            LOD1ButtonE.LODtoWrite = 1
        
        row = layout.row()
        if UEXPEditor.LOD2vStart != 0:
            row.label(text="LOD2: "+str(UEXPEditor.LOD2vStart)+" - "+str(UEXPEditor.LOD2vEnd), icon='MESH_ICOSPHERE')
            LOD2Button = row.operator("object.import_uexp", icon='MESH_ICOSPHERE')
            LOD2Button.LODtoLoad = 2
            LOD2ButtonE = row.operator("object.export_uexp", icon='SCRIPTPLUGINS')
            LOD2ButtonE.LODtoWrite = 2
       
        row = layout.row()
        if UEXPEditor.LOD3vStart != 0:
            row.label(text="LOD3: "+str(UEXPEditor.LOD3vStart)+" - "+str(UEXPEditor.LOD3vEnd), icon='MESH_ICOSPHERE')
            LOD3Button = row.operator("object.import_uexp", icon='MESH_ICOSPHERE')
            LOD3Button.LODtoLoad = 3
            LOD3ButtonE = row.operator("object.export_uexp", icon='SCRIPTPLUGINS')
            LOD3ButtonE.LODtoWrite = 3

    

def register():
    bpy.utils.register_class(UexpPanel)
    bpy.utils.register_class(ImportUexp)
    bpy.utils.register_class(ExportUexp)
    bpy.utils.register_class(SearchForOffsets)
    bpy.utils.register_class(UEXPSettings)
    bpy.types.Scene.UEXPEditor = bpy.props.PointerProperty(type=UEXPSettings)

def unregister():
    bpy.utils.unregister_class(UexpPanel)
    bpy.utils.unregister_class(ImportUexp)
    bpy.utils.unregister_class(ExportUexp)
    bpy.utils.unregister_class(SearchForOffsets)

if __name__ == "__main__":
    register()

