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

#Vertex Data can be of any LOD, as long as it's a block of floats.
#The beginning offset of the vertex data we want to edit
VertexBegin = 6061849
#This indicates the offset of the last vertex. 
#So after this offset you'd still have 12 bytes to give us the coords of the last vertex.
VertexEnd = 6471265

#Not implemented.
FaceBegin = 0 
FaceEnd = 0 

#####################################################################
'''only relevant functions so far are CreateMesh() and WriteMesh()'''
#####################################################################


#Read vertex data from uexp and create vertex cloud of it.
def CreateMesh():
    
    #Read 4 bytes and unpack a float out of it for X, 
    #read the next 4 for Y and the next for Z
    def ReadVertex(rOffset):
        with open (Uexp, 'rb') as f:
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
    for n in range(VertexBegin,VertexEnd,12):
        vIndex += 1
        v = ReadVertex(n)
        
        #We add the vertex read to the vList
        vList.append(v)
        #print(vIndex, " = ", v)

    #print(vList)

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

    vCloud = VCloud("Venator", vList)
    
    #We add the created object to a collection
    bpy.context.collection.objects.link(vCloud)

    



#This is where we write the modified vertex data back into the uexp
def WriteMesh():
    
    #Gotta have the object as active selected for this to work
    CreatedMesh = bpy.context.active_object.data

    #Returns the binary coordinates of the given vertex index. 
    def GetVCoords(index):
        
        #get coordinates of vertex
        x = CreatedMesh.vertices[index].co[0]
        y = CreatedMesh.vertices[index].co[1]
        z = CreatedMesh.vertices[index].co[2]
        
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
        with open (Uexp, 'rb+') as f:
            f.seek(vOffset)
            for i in vBinCoords:
                f.write(i)
        
        
    vIndex = -1
    #For each vertex we get its coordinates and write them to uexp.
    for n in range(VertexBegin, VertexEnd, 12):
        vIndex += 1
        vbCoords = GetVCoords(vIndex)
        WriteVBin(n,vbCoords)


        

#This is an attempt at finding the VertexBegin and VertexEnd offsets from an imported psk mesh
#Not quite working because 2 vertices can share the exact same coordinates.
#For first vertex it's not an issue since we retain the first found offset.
#But for last, it could fail.

#For now it's best to find vertex offsets manually in a hex editor.

#Select psk mesh before doing this.
def FindVertexOffsets():
    
    startOffset = 0
    endOffset = 0
    
    #We get the coordinates of the given vertex index.
    def GetVertexCo(vIndex):
        coords = []
        obData = bpy.context.active_object.data
        x = obData.vertices[vIndex].co[0]
        y = obData.vertices[vIndex].co[1]
        z = obData.vertices[vIndex].co[2]
        coords = [x,y,z]
        return coords
    
    #Get first vertex coordinates
    firstVertexCo = GetVertexCo(0)
    
    #Find what the last vertex index is.
    vertices = bpy.context.active_object.data.vertices
    lastVert = len(vertices)-1
    
    #Get last vertex coordinates
    lastVertexCo = GetVertexCo(lastVert)
    
    #Given the coordinates of a vertex, we try to find a match in the uexp
    #We go through the whole file byte by byte, reading 12 bytes and comparing with our coords.
    def SearchForVOffsets(offset,coords):
        with open (Uexp, 'rb') as f:
            #This holds the floats found in the uexp
            floatTriplet=[]
            
            f.seek(offset)
            
            #3 times we will read 4 bytes and unpack those as floats and add to the floatTriplet[]
            for n in range(3):
                bData = f.read(4)
                if len(bData)==4:
                    fData = struct.unpack('<f',bData)                        
                    floatTriplet.append(fData[0])
           
            #Check if found floats are equal to coords floats
            if floatTriplet == coords:                
                return offset
            else:
                return 0
    
    #This controls the SearchForVOffsets function, give it the needed offset. 
    for n in range(Size):
        #Here we supply the coordinates of the FIRST Vertex
        startOffset = SearchForVOffsets(n,firstVertexCo)
        #Break out of the loop if we find the offset
        if startOffset != 0:
            print(startOffset)
            break
    
    #We do it all again to find the offset of the last vertex coords
    for n in range(Size):
        startOffset = SearchForVOffsets(n,lastVertexCo)
        if endOffset != 0:
            print(endOffset)
            break
        
    return startOffset, endOffset


#This was an attempt at finding face data, did not work at all. 
#Face data should be stored as groups of 3 shorts (2 bytes representing an integer)
#The 3 shorts represent vertex indices forming a triangle.
#So what I did is get the face index 0 and get its 3 vertex indices and search through the uexp for them. 
#I could not find anything even when trying with random faces.
#even when trying with different index order.

#We want to find where face data starts and end in the uexp file
def FindFaceOffsets():
    
    startOffset = 0
    endOffset = 0
    
    #From the selected object (an imported psk) we get the vertices of polygon[0] 
    #and the last polygon
    def FindFirstLastFaceVertices():
        
        polygons = bpy.context.active_object.data.polygons
        lastFace = len(polygons)-1
        
        vs1 = polygons[0].vertices[0]
        vs2 = polygons[0].vertices[1]
        vs3 = polygons[0].vertices[2]
        fStart = [vs1,vs2,vs3]
        
        ve1 = polygons[lastFace].vertices[0]
        ve2 = polygons[lastFace].vertices[1]
        ve3 = polygons[lastFace].vertices[2]
        fEnd = [ve1,ve2,ve3]
        
        print(fStart, "...", fEnd)
        
        return fStart,fEnd
    
    fStart,fEnd = FindFirstLastFaceVertices()
    
    #read the entire file by block of 3 for each offset 
    #and see if we match our vertice indices.
    def SearchForIndices(offset,vGroup):
        with open (Uexp, 'rb') as f:
            
            intTriplet=[]
            
            f.seek(offset)
            
            #3 times we will read 2 bytes to unpack as a short (integer) 
            for n in range(3):
                bData = f.read(2)
                if len(bData)==2:
                    iData = struct.unpack('<H',bData)                        
                    intTriplet.append(iData[0])
           
            #print(intTriplet, "     ", vGroup)
            if intTriplet == vGroup:                
                return offset
            else:
                return 0
        
        
    
    #This controls the SearchForIndices function, gives it the needed offset. 
    for n in range (Size):
        #Here we supply the indices of the FIRST face
        startOffset = SearchForIndices(n,fStart)
        #Break out of the loop if we find the offset
        if startOffset != 0:
            print(startOffset)
            break

    #We do it all again to find the offset of the last face    
    for n in range (Size):
        endOffset = SearchForIndices(n,fEnd)
        if endOffset != 0:
            print(endOffset)
            break
        
        
    



##### PANEL UI STUFF #######

class EditUexp(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.edit_uexp"
    bl_label = "Import uexp"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        CreateMesh()
        return {'FINISHED'}
    
class ExportUexp(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.export_uexp"
    bl_label = "Export uexp"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        WriteMesh()
        return {'FINISHED'}




class UexpPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Uexp Panel"
    bl_idname = "OBJECT_PT_uexp"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        #row = layout.row()
        #row.label(text="Load uexp", icon='CONSTRAINT_BONE')
        row = layout.row()
        row.operator("object.edit_uexp", icon='SCRIPTPLUGINS')
        row = layout.row()
        row.operator("object.export_uexp", icon='SCRIPTPLUGINS')


def register():
    bpy.utils.register_class(UexpPanel)
    bpy.utils.register_class(EditUexp)
    bpy.utils.register_class(ExportUexp)

def unregister():
    bpy.utils.unregister_class(UexpPanel)
    bpy.utils.unregister_class(EditUexp)
    bpy.utils.unregister_class(ExportUexp)

if __name__ == "__main__":
    register()

