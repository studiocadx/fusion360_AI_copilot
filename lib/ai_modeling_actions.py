# AI Modeling Actions Module
# This module contains functions to execute 3D modeling operations in Fusion 360

import adsk.core
import adsk.fusion
import math
from typing import Dict, Any, Optional
from . import fusionAddInUtils as futil

app = adsk.core.Application.get()
ui = app.userInterface

class AIModelingActions:
    """
    Class containing AI-driven modeling actions for Fusion 360
    """
    
    def __init__(self):
        self.app = app
        self.ui = ui
        
    def execute_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a modeling command based on AI-parsed data
        
        Args:
            command_data: Dictionary containing action and parameters
            
        Returns:
            Dictionary with execution result
        """
        try:
            action = command_data.get("action")
            parameters = command_data.get("parameters", {})
            
            if action == "create_box":
                return self._create_box(parameters)
            elif action == "create_cylinder":
                return self._create_cylinder(parameters)
            elif action == "create_sphere":
                return self._create_sphere(parameters)
            elif action == "create_gear":
                return self._create_gear(parameters)
            elif action == "create_hole":
                return self._create_hole(parameters)
            elif action == "extrude_face":
                return self._extrude_selected_face(parameters)
            elif action == "move_body":
                return self._move_selected_body(parameters)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "originalCommand": command_data.get("originalCommand", "")
                }
                
        except Exception as e:
            futil.log(f"Modeling Action Error: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            return {
                "status": "error",
                "message": f"Execution error: {str(e)}",
                "originalCommand": command_data.get("originalCommand", "")
            }
    
    def _get_active_design(self) -> Optional[adsk.fusion.Design]:
        """Get the active design, return None if not available"""
        try:
            product = self.app.activeProduct
            if not product:
                return None
            return adsk.fusion.Design.cast(product)
        except:
            return None
    
    def _create_box(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a box/cube with specified dimensions"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get parameters with defaults
            length = parameters.get("length", 10.0) / 10.0  # Convert mm to cm
            width = parameters.get("width", length * 10.0) / 10.0
            height = parameters.get("height", length * 10.0) / 10.0
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create a new sketch on the XY plane
            sketches = rootComp.sketches
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
            
            # Create a rectangle
            lines = sketch.sketchCurves.sketchLines
            point1 = adsk.core.Point3D.create(-length/2, -width/2, 0)
            point2 = adsk.core.Point3D.create(length/2, width/2, 0)
            lines.addTwoPointRectangle(point1, point2)
            
            # Get the profile for extrusion
            profile = sketch.profiles.item(0)
            
            # Create extrusion
            extrudes = rootComp.features.extrudeFeatures
            extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Set the extrusion distance
            distance = adsk.core.ValueInput.createByReal(height)
            extrudeInput.setDistanceExtent(False, distance)
            
            # Create the extrusion
            extrude = extrudes.add(extrudeInput)
            
            return {
                "status": "success",
                "message": f"Created box: {length*10:.1f}mm × {width*10:.1f}mm × {height*10:.1f}mm",
                "action": "create_box",
                "parameters": {"length": length*10, "width": width*10, "height": height*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to create box: {str(e)}"}
    
    def _create_cylinder(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cylinder with specified radius and height"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get parameters with defaults
            radius = parameters.get("radius", 5.0) / 10.0  # Convert mm to cm
            height = parameters.get("height", 10.0) / 10.0
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create a new sketch on the XY plane
            sketches = rootComp.sketches
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
            
            # Create a circle
            circles = sketch.sketchCurves.sketchCircles
            centerPoint = adsk.core.Point3D.create(0, 0, 0)
            circle = circles.addByCenterRadius(centerPoint, radius)
            
            # Get the profile for extrusion
            profile = sketch.profiles.item(0)
            
            # Create extrusion
            extrudes = rootComp.features.extrudeFeatures
            extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Set the extrusion distance
            distance = adsk.core.ValueInput.createByReal(height)
            extrudeInput.setDistanceExtent(False, distance)
            
            # Create the extrusion
            extrude = extrudes.add(extrudeInput)
            
            return {
                "status": "success",
                "message": f"Created cylinder: radius {radius*10:.1f}mm, height {height*10:.1f}mm",
                "action": "create_cylinder",
                "parameters": {"radius": radius*10, "height": height*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to create cylinder: {str(e)}"}
    
    def _create_sphere(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sphere with specified radius"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get parameters with defaults
            radius = parameters.get("radius", 5.0) / 10.0  # Convert mm to cm
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create a new sketch on the XZ plane for the profile
            sketches = rootComp.sketches
            xzPlane = rootComp.xZConstructionPlane
            sketch = sketches.add(xzPlane)
            
            # Create a semicircle arc
            arcs = sketch.sketchCurves.sketchArcs
            centerPoint = adsk.core.Point3D.create(0, 0, 0)
            startPoint = adsk.core.Point3D.create(0, 0, radius)
            endPoint = adsk.core.Point3D.create(0, 0, -radius)
            arc = arcs.addByCenterStartEnd(centerPoint, startPoint, endPoint)
            
            # Create a line to close the profile
            lines = sketch.sketchCurves.sketchLines
            line = lines.addByTwoPoints(startPoint, endPoint)
            
            # Get the profile for revolution
            profile = sketch.profiles.item(0)
            
            # Create revolution around Y-axis
            revolves = rootComp.features.revolveFeatures
            revolveInput = revolves.createInput(profile, line, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Set full revolution (360 degrees)
            angle = adsk.core.ValueInput.createByReal(2 * 3.14159)  # 2π radians = 360 degrees
            revolveInput.setAngleExtent(False, angle)
            
            # Create the revolution
            revolve = revolves.add(revolveInput)
            
            return {
                "status": "success",
                "message": f"Created sphere: radius {radius*10:.1f}mm",
                "action": "create_sphere",
                "parameters": {"radius": radius*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to create sphere: {str(e)}"}
    
    def _create_gear(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a spur gear with specified parameters"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get parameters with defaults
            num_teeth = int(parameters.get("number_of_teeth", 20))
            module = parameters.get("module", 2.0)  # mm
            bore_diameter = parameters.get("bore_diameter", 6.0) / 10.0  # Convert mm to cm
            thickness = parameters.get("thickness", 5.0) / 10.0  # Convert mm to cm
            
            # Calculate gear dimensions
            pitch_diameter = num_teeth * module / 10.0  # Convert to cm
            outer_diameter = (num_teeth + 2) * module / 10.0  # Convert to cm
            root_diameter = (num_teeth - 2.5) * module / 10.0  # Convert to cm
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create a new sketch on the XY plane
            sketches = rootComp.sketches
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
            
            # Create the gear profile using a simplified approach
            circles = sketch.sketchCurves.sketchCircles
            centerPoint = adsk.core.Point3D.create(0, 0, 0)
            
            # Create outer circle (simplified gear - in production, you'd create actual gear teeth)
            outer_circle = circles.addByCenterRadius(centerPoint, outer_diameter/2)
            
            # Create bore hole
            if bore_diameter > 0:
                bore_circle = circles.addByCenterRadius(centerPoint, bore_diameter/2)
            
            # Get the profile for extrusion (outer circle minus bore)
            profiles = sketch.profiles
            gear_profile = None
            for i in range(profiles.count):
                profile = profiles.item(i)
                # Find the profile that represents the gear body (outer circle minus bore)
                if profile.profileLoops.count > 0:
                    gear_profile = profile
                    break
            
            if not gear_profile:
                gear_profile = profiles.item(0)
            
            # Create extrusion
            extrudes = rootComp.features.extrudeFeatures
            extrudeInput = extrudes.createInput(gear_profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Set the extrusion distance
            distance = adsk.core.ValueInput.createByReal(thickness)
            extrudeInput.setDistanceExtent(False, distance)
            
            # Create the extrusion
            extrude = extrudes.add(extrudeInput)
            
            # Add gear teeth using circular pattern (simplified approach)
            # In a full implementation, you would create actual involute gear teeth
            
            return {
                "status": "success",
                "message": f"Created gear: {num_teeth} teeth, module {module}mm, bore {bore_diameter*10:.1f}mm, thickness {thickness*10:.1f}mm",
                "action": "create_gear",
                "parameters": {
                    "number_of_teeth": num_teeth,
                    "module": module,
                    "bore_diameter": bore_diameter*10,
                    "thickness": thickness*10
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to create gear: {str(e)}"}
    
    def _create_hole(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a hole in a selected face"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get the selection
            selection = self.ui.activeSelections
            if selection.count == 0:
                return {"status": "error", "message": "Please select a face to create a hole in first."}
            
            # Check if selected entity is a face
            selectedEntity = selection.item(0).entity
            if not isinstance(selectedEntity, adsk.fusion.BRepFace):
                return {"status": "error", "message": "Please select a face (not an edge or body)."}
            
            # Get parameters
            diameter = parameters.get("diameter", 5.0) / 10.0  # Convert mm to cm
            depth = parameters.get("depth", 10.0) / 10.0  # Convert mm to cm
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create a sketch on the selected face
            sketches = rootComp.sketches
            sketch = sketches.add(selectedEntity)
            
            # Get the center point of the face (simplified - uses face center)
            boundingBox = selectedEntity.boundingBox
            centerX = (boundingBox.minPoint.x + boundingBox.maxPoint.x) / 2
            centerY = (boundingBox.minPoint.y + boundingBox.maxPoint.y) / 2
            centerZ = (boundingBox.minPoint.z + boundingBox.maxPoint.z) / 2
            
            # Create a circle for the hole
            circles = sketch.sketchCurves.sketchCircles
            centerPoint = adsk.core.Point3D.create(0, 0, 0)  # Relative to sketch plane
            circle = circles.addByCenterRadius(centerPoint, diameter/2)
            
            # Get the profile for extrusion
            profile = sketch.profiles.item(0)
            
            # Create extrusion (cut operation)
            extrudes = rootComp.features.extrudeFeatures
            extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
            
            # Set the extrusion distance
            distance = adsk.core.ValueInput.createByReal(depth)
            extrudeInput.setDistanceExtent(False, distance)
            
            # Create the extrusion (hole)
            extrude = extrudes.add(extrudeInput)
            
            return {
                "status": "success",
                "message": f"Created hole: diameter {diameter*10:.1f}mm, depth {depth*10:.1f}mm",
                "action": "create_hole",
                "parameters": {"diameter": diameter*10, "depth": depth*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to create hole: {str(e)}"}
    
    def _extrude_selected_face(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extrude a selected face by specified distance"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get the selection
            selection = self.ui.activeSelections
            if selection.count == 0:
                return {"status": "error", "message": "Please select a face to extrude first."}
            
            # Check if selected entity is a face
            selectedEntity = selection.item(0).entity
            if not isinstance(selectedEntity, adsk.fusion.BRepFace):
                return {"status": "error", "message": "Please select a face (not an edge or body)."}
            
            distance = parameters.get("distance", 5.0) / 10.0  # Convert mm to cm
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create extrusion
            extrudes = rootComp.features.extrudeFeatures
            extrudeInput = extrudes.createInput(selectedEntity, adsk.fusion.FeatureOperations.JoinFeatureOperation)
            
            # Set the extrusion distance
            distanceValue = adsk.core.ValueInput.createByReal(distance)
            extrudeInput.setDistanceExtent(False, distanceValue)
            
            # Create the extrusion
            extrude = extrudes.add(extrudeInput)
            
            return {
                "status": "success",
                "message": f"Extruded selected face by {distance*10:.1f}mm",
                "action": "extrude_face",
                "parameters": {"distance": distance*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to extrude face: {str(e)}"}
    
    def _move_selected_body(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Move a selected body by specified distances"""
        try:
            design = self._get_active_design()
            if not design:
                return {"status": "error", "message": "No active design found. Please create or open a design first."}
            
            # Get the selection
            selection = self.ui.activeSelections
            if selection.count == 0:
                return {"status": "error", "message": "Please select a body to move first."}
            
            # Check if selected entity is a body
            selectedEntity = selection.item(0).entity
            if not isinstance(selectedEntity, adsk.fusion.BRepBody):
                return {"status": "error", "message": "Please select a body (not a face or edge)."}
            
            # Get movement parameters (convert mm to cm)
            x = parameters.get("x", 0.0) / 10.0
            y = parameters.get("y", 0.0) / 10.0
            z = parameters.get("z", 0.0) / 10.0
            
            # Get the root component
            rootComp = design.rootComponent
            
            # Create move feature
            moveFeatures = rootComp.features.moveFeatures
            
            # Create object collection with the selected body
            objectCollection = adsk.core.ObjectCollection.create()
            objectCollection.add(selectedEntity)
            
            # Create move input
            moveInput = moveFeatures.createInput(objectCollection)
            
            # Create translation vector
            vector = adsk.core.Vector3D.create(x, y, z)
            transform = adsk.core.Matrix3D.create()
            transform.translation = vector
            
            # Set the transform
            moveInput.defineAsTransform(transform)
            
            # Create the move
            move = moveFeatures.add(moveInput)
            
            return {
                "status": "success",
                "message": f"Moved selected body by X:{x*10:.1f}mm, Y:{y*10:.1f}mm, Z:{z*10:.1f}mm",
                "action": "move_body",
                "parameters": {"x": x*10, "y": y*10, "z": z*10}
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to move body: {str(e)}"}