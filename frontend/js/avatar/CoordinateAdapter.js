class AvatarCoordinateAdapter {
    /**
     * Converts a semantic arm pose to Three.js Quaternions.
     * Coordinate System: +Y up, -Y down, +Z toward viewer, -Z behind, +X right, -X left.
     * @param {string} side 'left' or 'right'
     * @param {Array} armAngles [pitch, abduction, yaw, elbowFlex, wristPitch, wristYaw, wristRoll]
     * @returns {Object} { shoulderQuat, elbowQuat, wristQuat }
     */
    static convertArmPose(side, armAngles) {
        if (!armAngles || armAngles.length < 4) return null;
        
        const sideSign = (side === 'left') ? 1 : -1;
        
        // 0: shoulder pitch (elevation forward toward chest/face)
        const pitch = Math.max(-0.4, Math.min(2.2, armAngles[0] || 0));
        
        // 1: shoulder abduction (positive = moves outward away from body)
        const abduct = armAngles[1] || 0;
        
        // 2: shoulder yaw / internal rotation
        const yaw = armAngles[2] || 0;
        
        // Convert to local bone Euler angles based on correct coordinate system
        // Pitch uses -X to move the -Y arm forward (+Z).
        // Abduction uses sideSign * Z to move outward.
        // Yaw uses sideSign * Y for internal rotation.
        const shoulderEuler = new THREE.Euler(-pitch, sideSign * yaw, sideSign * abduct, 'XYZ');
        const shoulderQuat = new THREE.Quaternion().setFromEuler(shoulderEuler);

        // 3: elbow flexion (bending forearm forward/upward toward chest)
        const elbowFlex = Math.max(0.0, Math.min(2.4, armAngles[3] || 0));
        const elbowEuler = new THREE.Euler(-elbowFlex, 0, 0, 'XYZ');
        const elbowQuat = new THREE.Quaternion().setFromEuler(elbowEuler);

        // 4,5,6: wrist pitch, yaw, roll
        const wristPitch = armAngles[4] || 0;
        const wristYaw = armAngles[5] || 0;
        const wristRoll = armAngles[6] || 0;
        const wristEuler = new THREE.Euler(-wristPitch, sideSign * wristYaw, sideSign * wristRoll, 'XYZ');
        const wristQuat = new THREE.Quaternion().setFromEuler(wristEuler);

        return { shoulderQuat, elbowQuat, wristQuat };
    }

    /**
     * Converts semantic finger curls [0.0 to 1.0] to Quaternions.
     * @param {string} side 'left' or 'right'
     * @param {Array} fingerCurls [thumb, index, middle, ring, pinky]
     * @returns {Object} Quaternions for MCP and PIP joints
     */
    static convertHandPose(side, fingerCurls) {
        if (!fingerCurls || fingerCurls.length !== 5) return null;
        const sideSign = (side === 'left') ? 1 : -1;
        
        const result = {};
        const fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
        
        fingers.forEach((name, idx) => {
            const curl = Math.max(0.0, Math.min(1.0, fingerCurls[idx] || 0.0));
            
            let mcpEuler, pipEuler;
            if (name === 'Thumb') {
                mcpEuler = new THREE.Euler(-curl * 0.8, sideSign * curl * 0.9, 0, 'XYZ');
                pipEuler = new THREE.Euler(-curl * 1.1, 0, 0, 'XYZ');
            } else {
                mcpEuler = new THREE.Euler(-curl * 1.25, 0, 0, 'XYZ');
                pipEuler = new THREE.Euler(-curl * 1.35, 0, 0, 'XYZ');
            }
            
            result[name] = {
                mcpQuat: new THREE.Quaternion().setFromEuler(mcpEuler),
                pipQuat: new THREE.Quaternion().setFromEuler(pipEuler)
            };
        });
        
        return result;
    }
}
