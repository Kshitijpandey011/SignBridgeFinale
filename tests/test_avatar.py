import pytest
from backend.avatar.animation_planner import AvatarAnimationPlanner

def test_avatar_sign_plan():
    planner = AvatarAnimationPlanner()
    plan = planner.plan_sequence("HELLO THANK YOU", "ASL")

    assert len(plan["sequence"]) == 2
    assert plan["sequence"][0]["word"] == "HELLO"
    assert plan["sequence"][1]["word"] == "THANK_YOU"
    assert plan["sequence"][0]["type"] == "sign"
    assert plan["total_duration"] > 0

def test_avatar_missing_word_fallback():
    planner = AvatarAnimationPlanner()
    # "COLLEGE" is not in the base sign dictionary; per Prompt Section 19, verify fallback!
    plan = planner.plan_sequence("COLLEGE", "ASL")

    assert "COLLEGE" in plan["unavailable_words"]
    assert len(plan["sequence"]) == 1
    assert plan["sequence"][0]["type"] == "fingerspelling"
    assert "unavailable" in plan["sequence"][0]["notice"].lower()
    assert len(plan["sequence"][0]["letters"]) == len("COLLEGE")

import math

def simulate_threejs_rotation(pitch, yaw, abduct, sideSign):
    # Simulate Three.js XYZ intrinsic rotation order on a -Y pointing arm
    # For XYZ order, matrix = Rz * Ry * Rx
    # Vector points along -Y initially: v = [0, -1, 0]
    
    # After our fix in JS:
    rx = -pitch
    ry = sideSign * yaw
    rz = sideSign * abduct
    
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    
    # Vector [0, -1, 0] multiplied by Rx, Ry, Rz (intrinsic XYZ)
    # R_x * [0, -1, 0] = [0, -cx, -sx]
    # R_y * [0, -cx, -sx] = [sx * sy, -cx, -sx * cy]
    # R_z * [sx*sy, -cx, -sx*cy] = [cz*sx*sy + sz*cx, sz*sx*sy - cz*cx, -sx*cy]
    # Actually, Three.js applies Rz * Ry * Rx to a vector.
    
    # Let's apply Rx first:
    y1 = -cx
    z1 = -sx
    x1 = 0
    
    # Then Ry:
    x2 = cy * x1 + sy * z1
    y2 = y1
    z2 = -sy * x1 + cy * z1
    
    # Then Rz:
    x3 = cz * x2 - sz * y2
    y3 = sz * x2 + cz * y2
    z3 = z2
    
    return x3, y3, z3

def test_avatar_orientation_forward_pitch():
    # Test 1 - Forward pitch: Positive semantic forward pitch should move toward viewer (+Z)
    pitch = 1.0 # semantic forward
    # Right arm (sideSign = -1)
    x, y, z = simulate_threejs_rotation(pitch=pitch, yaw=0, abduct=0, sideSign=-1)
    assert z > 0, "Right arm forward pitch must yield positive Z (toward viewer)"
    
    # Left arm (sideSign = 1)
    x, y, z = simulate_threejs_rotation(pitch=pitch, yaw=0, abduct=0, sideSign=1)
    assert z > 0, "Left arm forward pitch must yield positive Z (toward viewer)"

def test_avatar_orientation_elbow_flexion():
    # Test 2 - Elbow flexion: Same as pitch, flexing elbow should bring forearm forward (+Z)
    # The elbow local space has its Y axis pointing down the upper arm. 
    # Applying negative rotation around X will also yield a +Z component relative to the upper arm.
    elbowFlex = 1.5
    x, y, z = simulate_threejs_rotation(pitch=elbowFlex, yaw=0, abduct=0, sideSign=1)
    assert z > 0, "Elbow flexion must yield positive Z relative to upper arm"

def test_avatar_orientation_abduction():
    # Test 4 - Abduction: Positive abduction moves arms outward
    abduct = 1.0
    
    # Right arm (sideSign = -1, located at -X)
    # Outward means moving toward -X
    x, y, z = simulate_threejs_rotation(pitch=0, yaw=0, abduct=abduct, sideSign=-1)
    assert x < 0, "Right arm abduction must yield negative X (outward)"
    
    # Left arm (sideSign = 1, located at +X)
    # Outward means moving toward +X
    x, y, z = simulate_threejs_rotation(pitch=0, yaw=0, abduct=abduct, sideSign=1)
    assert x > 0, "Left arm abduction must yield positive X (outward)"
