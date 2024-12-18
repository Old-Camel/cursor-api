const { randomBytes, createHash } = require('crypto');

function generateHashed64Hex() {
    const randomData = randomBytes(32);
    const hash = createHash("sha256");
    hash.update(randomData);
    return hash.digest("hex");
}

function C(byteArray) {
    let t = 165;
    for (let r = 0; r < byteArray.length; r++) {
        byteArray[r] = (byteArray[r] ^ t) + (r % 256);
        t = byteArray[r];
    }
    return byteArray;
}

function base64Fn(byteArray) {
    return btoa(String.fromCharCode.apply(null, byteArray));
}

function generateCursorChecksum(machineId, macMachineId) {
    const timestamp = Math.floor(Date.now() / 1e6);
    const byteArray = new Uint8Array([
        (timestamp >> 40) & 255,
        (timestamp >> 32) & 255,
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        255 & timestamp,
    ]);

    const obfuscatedBytes = C(byteArray);
    const encodedChecksum = base64Fn(obfuscatedBytes);

    const checksum = macMachineId
        ? `${encodedChecksum}${machineId}/${macMachineId}`
        : `${encodedChecksum}${machineId}`;

    return checksum;
}

module.exports = {
    generateHashed64Hex,
    generateCursorChecksum
}; 