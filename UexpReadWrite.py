import bpy
import bmesh

import os
import sys
import struct

#The code basically reads bytes by group of 4 to get floats. 
#3 floats read give us the x,y,z coordinates of a vertex. 
#We then create that vertex in a mesh, and repeat for all vertices.
#Once the mesh edited we do the opposite
#Get the float coordinates of a vertex and write it to the uexp as bytes.


#Path to the uexp, needs the double \\ to work.
Uexp = "A:\\Fallen Order Modding\\ModCalFace\\SwGame\\Content\\Characters\\Hero\\Rig\\Face\\hero_rig_face.uexp"
Size = os.path.getsize(Uexp)

#Not implemented.
FaceBegin = 0 
FaceEnd = 0 

class UEXPSettings(bpy.types.PropertyGroup):
    LOD0vStart: bpy.props.IntProperty()
    LOD0vEnd: bpy.props.IntProperty()
    LOD1vStart: bpy.props.IntProperty()
    LOD1vEnd: bpy.props.IntProperty()
    LOD2vStart: bpy.props.IntProperty()
    LOD2vEnd: bpy.props.IntProperty()
    LOD3vStart: bpy.props.IntProperty()
    LOD3vEnd : bpy.props.IntProperty()

#Read vertex data from uexp and create vertex cloud of it.
def CreateMesh(LOD):
    UEXPEditor = bpy.data.scenes['Scene'].UEXPEditor
    if LOD == 0:
        LODvStart = UEXPEditor.LOD0vStart
        LODvEnd = UEXPEditor.LOD0vEnd
        LODsuffix="_LOD0"
    if LOD == 1:
        LODvStart = UEXPEditor.LOD1vStart
        LODvEnd = UEXPEditor.LOD1vEnd
        LODsuffix="_LOD1"
    if LOD == 2:
        LODvStart = UEXPEditor.LOD2vStart
        LODvEnd = UEXPEditor.LOD2vEnd
        LODsuffix="_LOD2"
    if LOD == 3:
        LODvStart = UEXPEditor.LOD3vStart
        LODvEnd = UEXPEditor.LOD3vEnd
        LODsuffix="_LOD3"
    
    
    with open (Uexp, 'rb') as f:
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

        vIndex = -1
        vList = []

        #For each vertex we ask ReadVertex() to give us the coordinates.
        #We move by steps of 12 bytes (3 floats)
        for n in range(LODvStart,LODvEnd-12,12):
            vIndex += 1
            v = ReadVertex(n)
            #We add the vertex read to the vList
            vList.append(v)

    #Create vertex cloud
    def VCloud(object_name, coords, edges=[],faces=[]):
        
        #Create a mesh
        mesh = bpy.data.meshes.new(object_name+"Mesh")
        #Create an object with our created mesh assigned.
        object = bpy.data.objects.new(object_name, mesh)
        
        #This is where we construct the mesh by supplying vertex coords, edges and faces
        #For now only coords is implemented.
        mesh.from_pydata(coords, edges, faces)
              
        object.show_name = True
        
        #gotta update to confirm mesh creation
        mesh.update()
        return object

    vCloud = VCloud("AT-ST"+LODsuffix, vList)
    
    #We add the created object to a collection
    bpy.context.collection.objects.link(vCloud)

    



#This is where we write the modified vertex data back into the uexp
def WriteMesh():
    return
    
#    #Gotta have the object as active selected for this to work
#    CreatedMesh = bpy.context.active_object.data

#    #Returns the binary coordinates of the given vertex index. 
#    def GetVCoords(index):
#        
#        #get coordinates of vertex
#        x = CreatedMesh.vertices[index].co[0]
#        y = CreatedMesh.vertices[index].co[1]
#        z = CreatedMesh.vertices[index].co[2]
#        
#        #turn these float coordinates into bytes
#        xb = struct.pack('<f',x)
#        yb = struct.pack('<f',y)
#        zb = struct.pack('<f',z)
#        
#        #binary vertex coordinates
#        vb = [xb,yb,zb]
#        
#        #print (xb,yb,zb)
#        return vb
#    
#    #Write the new binary vertex coordinates to the uexp
#    def WriteVBin(vOffset,vBinCoords):
#        with open (Uexp, 'rb+') as f:
#            f.seek(vOffset)
#            for i in vBinCoords:
#                f.write(i)
#        
#        
#    vIndex = -1
#    #For each vertex we get its coordinates and write them to uexp.
#    for n in range(VertexBegin, VertexEnd, 12):
#        vIndex += 1
#        vbCoords = GetVCoords(vIndex)
#        WriteVBin(n,vbCoords)


#Finds start and end offsets of vertex data
def FindVertexOffsets(SearchOffset):
    
    startOffset = 0
    endOffset = 0
    
    #We go through the whole file byte by byte, 
    #reading 12 bytes trying to find 2 sets of interlocking int
    with open (Uexp, 'rb') as f:
        for n in range(SearchOffset,Size):            
            f.seek(n)
            int1 = f.read(4)
            intA = f.read(4)
            int2 = f.read(4)
            intB = f.read(4)
            
            if len(intA)==4:
                itemsize = struct.unpack('<i',int1)
                #print(itemsize)
                vertcount = struct.unpack('<i',intA)
                
                if itemsize[0] == 12 and vertcount[0] > 3:
                    if int1 == int2 and intA == intB:
                        vdatalength = itemsize[0]*vertcount[0]
                        if vdatalength < Size-n:
                            f.seek(vdatalength,1)
                            offset = f.tell()
                            #print(offset)
                            #print(vdatalength,itemsize[0],vertcount[0])
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




#This was an attempt at finding face data, did not work at all. 
#Face data should be stored as groups of 3 shorts (2 bytes representing an integer)
#The 3 shorts represent vertex indices forming a triangle.
#So what I did is get the face index 0 and get its 3 vertex indices and search through the uexp for them. 
#I could not find anything even when trying with random faces.
#even when trying with different index order.

#We want to find where face data starts and end in the uexp file
#def FindFaceOffsets():
#    
#    startOffset = 0
#    endOffset = 0
#    
#    #From the selected object (an imported psk) we get the vertices of polygon[0] 
#    #and the last polygon
#    def FindFirstLastFaceVertices():
#        
#        polygons = bpy.context.active_object.data.polygons
#        lastFace = len(polygons)-1
#        
#        vs1 = polygons[0].vertices[0]
#        vs2 = polygons[0].vertices[1]
#        vs3 = polygons[0].vertices[2]
#        fStart = [vs1,vs2,vs3]
#        
#        ve1 = polygons[lastFace].vertices[0]
#        ve2 = polygons[lastFace].vertices[1]
#        ve3 = polygons[lastFace].vertices[2]
#        fEnd = [ve1,ve2,ve3]
#        
#        print(fStart, "...", fEnd)
#        
#        return fStart,fEnd
#    
#    fStart,fEnd = FindFirstLastFaceVertices()
#    
#    #read the entire file by block of 3 for each offset 
#    #and see if we match our vertice indices.
#    def SearchForIndices(offset,vGroup):
#        with open (Uexp, 'rb') as f:
#            
#            intTriplet=[]
#            
#            f.seek(offset)
#            
#            #3 times we will read 2 bytes to unpack as a short (integer) 
#            for n in range(3):
#                bData = f.read(2)
#                if len(bData)==2:
#                    iData = struct.unpack('<H',bData)                        
#                    intTriplet.append(iData[0])
#           
#            #print(intTriplet, "     ", vGroup)
#            if intTriplet == vGroup:                
#                return offset
#            else:
#                return 0
#        
#        
#    
#    #This controls the SearchForIndices function, gives it the needed offset. 
#    for n in range (Size):
#        #Here we supply the indices of the FIRST face
#        startOffset = SearchForIndices(n,fStart)
#        #Break out of the loop if we find the offset
#        if startOffset != 0:
#            print(startOffset)
#            break

#    #We do it all again to find the offset of the last face    
#    for n in range (Size):
#        endOffset = SearchForIndices(n,fEnd)
#        if endOffset != 0:
#            print(endOffset)
#            break
        
      
        
def SearchLODOffsets(LOD=0):
    UEXPEditor = bpy.data.scenes['Scene'].UEXPEditor
    
    if LOD >= 0:
        UEXPEditor.LOD0vStart,UEXPEditor.LOD0vEnd = FindVertexOffsets(0)
    if LOD >= 1:
        UEXPEditor.LOD1vStart,UEXPEditor.LOD1vEnd = FindVertexOffsets(UEXPEditor.LOD0vStart)
    if LOD >= 2:
        UEXPEditor.LOD2vStart,UEXPEditor.LOD2vEnd = FindVertexOffsets(UEXPEditor.LOD1vStart)
    if LOD >= 3:
        UEXPEditor.LOD3vStart,UEXPEditor.LOD3vEnd = FindVertexOffsets(UEXPEditor.LOD2vStart)
    
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
        WriteMesh()
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
        UEXPEditor = bpy.data.scenes['Scene'].UEXPEditor
        obj = context.object

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

