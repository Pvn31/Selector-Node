bl_info = {
    "name": "Selector",
    "author": "Pvn31",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Shader Editor>Add>Custom Nodes>Selector",
    "description": "Need some Good Description",
    "warning": "",
    "doc_url": "",
    "category": "Node",
}

import bpy

class UnitSelection(bpy.types.ShaderNodeCustomGroup):

    bl_name='Unit_Selection'
    bl_label='Unit Selection'       

    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        self.node_tree.inputs.new("NodeSocketFloat", "Input Value")
        self.node_tree.outputs.new("NodeSocketFloat", "Value")

    # Manage the internal nodes to perform the chained operation - clear all the nodes and build from scratch each time.
    def __nodetree_setup__(self):
        
        groupinput = self.node_tree.nodes['Group Input']
        
        mul1 = self.node_tree.nodes.new('ShaderNodeMath')
        mul1.name = 'MULTIPLY1'
        mul1.operation = 'MULTIPLY'
        mul1.inputs[0].default_value = self.NodeIndex
        mul1.inputs[1].default_value = 1/self.Total
        
        lessthan = self.node_tree.nodes.new('ShaderNodeMath')
        lessthan.operation = 'LESS_THAN'
        self.node_tree.links.new(groupinput.outputs[0],lessthan.inputs[0])
        self.node_tree.links.new(mul1.outputs[0],lessthan.inputs[1])

        compare = self.node_tree.nodes.new('ShaderNodeMath')
        compare.operation = 'COMPARE'
        self.node_tree.links.new(groupinput.outputs[0],compare.inputs[0])
        self.node_tree.links.new(mul1.outputs[0],compare.inputs[1])
        
        add = self.node_tree.nodes.new('ShaderNodeMath')
        add.operation = 'ADD'
        self.node_tree.links.new(lessthan.outputs[0],add.inputs[0])
        self.node_tree.links.new(compare.outputs[0],add.inputs[1])
        
        mul2 = self.node_tree.nodes.new('ShaderNodeMath')
        mul2.name = 'MULTIPLY2'
        mul2.operation = 'MULTIPLY'
        mul2.inputs[0].default_value = self.NodeIndex -1 
        mul2.inputs[1].default_value = 1/self.Total
        
        greaterthan = self.node_tree.nodes.new('ShaderNodeMath')
        greaterthan.operation = 'GREATER_THAN'
        self.node_tree.links.new(groupinput.outputs[0],greaterthan.inputs[0])
        self.node_tree.links.new(mul2.outputs[0],greaterthan.inputs[1])     

        
        mul3 = self.node_tree.nodes.new('ShaderNodeMath')
        mul3.operation = 'MULTIPLY'
        self.node_tree.links.new(add.outputs[0],mul3.inputs[0])
        self.node_tree.links.new(greaterthan.outputs[0],mul3.inputs[1])     
        
        # Connect the last one to the output
        self.node_tree.links.new(mul3.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])
    
    def update_values(self, context):
        mul1 = self.node_tree.nodes['MULTIPLY1']
        mul1.inputs[0].default_value = self.NodeIndex
        mul1.inputs[1].default_value = 1/self.Total
        
        mul2 = self.node_tree.nodes['MULTIPLY2']
        mul2.inputs[0].default_value = self.NodeIndex -1 
        mul2.inputs[1].default_value = 1/self.Total
        
    # for blender 2.80, the following properties should be annotation
    NodeIndex:bpy.props.IntProperty(name="Index", min=1, max=63, default=1, update = update_values)
    Total:bpy.props.IntProperty(name="Index", min=1, max=63, default=1, update = update_values)

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        self.node_tree=bpy.data.node_groups.new('.' + self.bl_name, 'ShaderNodeTree')
        self.node_tree.nodes.new('NodeGroupInput')
        self.node_tree.nodes.new('NodeGroupOutput')
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

    # Draw the node components
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, 'NodeIndex', text='Index of')
        row=layout.row()
        row.prop(self, 'Total', text='Total')

    # Copy
    def copy(self, node):
        self.node_tree=node.node_tree.copy()

    # Free (when node is deleted)
    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)



# for blender2.80 we should derive the class from bpy.types.ShaderNodeCustomGroup
class Selector(bpy.types.ShaderNodeCustomGroup):

    bl_name='Selector'
    bl_label='Selector Node'       

    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):

        # No operators --> no input or output sockets
        if self.Total < 1:
            self.node_tree.inputs.clear()
            self.node_tree.outputs.clear()
            return

        # Look for input sockets that are no longer required and remove them
        for i in range(len(self.node_tree.inputs),0,-1):
            if i > self.Total:
                print("removing ",i)
                self.node_tree.inputs.remove(self.node_tree.inputs[-1])

        # Add any additional input sockets that are now required
        for i in range(0, self.Total+1):
            if i+1 > len(self.node_tree.inputs):
                self.node_tree.inputs.new("NodeSocketColor", "Color")

        # Add the output socket
        if len(self.node_tree.outputs) < 1:
            self.node_tree.outputs.new("NodeSocketColor", "Color")

    # Manage the internal nodes to perform the chained operation - clear all the nodes and build from scratch each time.
    def __nodetree_setup__(self):

        # Remove all links and all nodes that aren't Group Input or Group Output
        self.node_tree.links.clear()
        for node in self.node_tree.nodes:
            if not node.name in ['Group Input','Group Output']:
                self.node_tree.nodes.remove(node)

        # Start from Group Input and add nodes as required, chaining each new one to the previous level and the next input
        groupinput = self.node_tree.nodes['Group Input']
        addnode = None
        
        maprange = self.node_tree.nodes.new('ShaderNodeMapRange')
        maprange.clamp = True
        self.node_tree.links.new(groupinput.outputs[0],maprange.inputs[0])
        maprange.inputs[2].default_value = self.Total
        
        if self.Total <= 1:
            # Special case <= 1 input --> link input directly to output
            self.node_tree.links.new(previousnode.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])
        else:
            # Create one node for each input socket > 1
            for i in range(1, self.Total):
                unitnode = self.node_tree.nodes.new('UnitSelection')
                unitnode.Total = self.Total
                unitnode.NodeIndex = i
                self.node_tree.links.new(maprange.outputs[0],unitnode.inputs[0])
                
                
                mixrgb_mul = self.node_tree.nodes.new('ShaderNodeMixRGB')
                mixrgb_mul.blend_type = 'MULTIPLY'
                mixrgb_mul.inputs[0].default_value = 1
                self.node_tree.links.new(groupinput.outputs[i],mixrgb_mul.inputs[1])
                self.node_tree.links.new(unitnode.outputs[0],mixrgb_mul.inputs[2])
                
                mixrgb_add = self.node_tree.nodes.new('ShaderNodeMixRGB')
                mixrgb_add.blend_type = 'ADD'
                mixrgb_add.inputs[0].default_value = 1
                #for the connection of add
                if(addnode):
                    self.node_tree.links.new(addnode.outputs[0],mixrgb_add.inputs[1])
                else:
                    self.node_tree.links.new(mixrgb_mul.outputs[0],mixrgb_add.inputs[1])
                
                if(addnode):
                     self.node_tree.links.new(mixrgb_mul.outputs[0],addnode.inputs[2])   
                
                addnode = mixrgb_add
            
            #last loop and connection because add is 1 less    
            unitnode = self.node_tree.nodes.new('UnitSelection')
            unitnode.Total = self.Total
            unitnode.NodeIndex = i+1
            self.node_tree.links.new(maprange.outputs[0],unitnode.inputs[0])
                
            mixrgb_mul = self.node_tree.nodes.new('ShaderNodeMixRGB')
            mixrgb_mul.blend_type = 'MULTIPLY'
            mixrgb_mul.inputs[0].default_value = 1
            self.node_tree.links.new(groupinput.outputs[i+1],mixrgb_mul.inputs[1])
            self.node_tree.links.new(unitnode.outputs[0],mixrgb_mul.inputs[2])
            
            self.node_tree.links.new(mixrgb_mul.outputs[0],addnode.inputs[2])
            # Connect the last one to the output
            self.node_tree.links.new(addnode.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])

    # Chosen operator has changed - update the nodes and links

    # Number of inputs has changed - update the nodes and links
    def update_inpSockets(self, context):
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

    # The node properties - Operator (Add, Subtract, etc.) and number of input sockets
    # for blender 2.80, the following properties should be annotation
    Total:bpy.props.IntProperty(name="Inputs", min=2, max=63, default=2, update=update_inpSockets)

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        self.node_tree=bpy.data.node_groups.new('.' + self.bl_name, 'ShaderNodeTree')
        self.node_tree.nodes.new('NodeGroupInput')
        self.node_tree.nodes.new('NodeGroupOutput')
        self.node_tree.inputs.new("NodeSocketFloat", "Current")
        self.__nodeinterface_setup__()
        self.__nodetree_setup__() 

    # Draw the node components
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, 'Total', text='Total')

    # Copy
    def copy(self, node):
        self.node_tree=node.node_tree.copy()

    # Free (when node is deleted)
    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
# in blender2.80 use ShaderNodeCategory
from nodeitems_builtins import ShaderNodeCategory

def register():
    bpy.utils.register_class(UnitSelection)
    bpy.utils.register_class(Selector)
    newcatlist = [ShaderNodeCategory("SH_NEW_CUSTOM", "Custom Nodes", items=[NodeItem("Selector"),]),]
    register_node_categories("CUSTOM_NODES", newcatlist)

def unregister():
    unregister_node_categories("CUSTOM_NODES")
    bpy.utils.unregister_class(Selector)
    bpy.utils.unregister_class(UnitSelection)
## Attempt to unregister our class (in case it's already been registered before) and register it.
#try :
#    unregister()
#    print("Unregistered")
#except:
#    print("Pass")
#    pass
#register()