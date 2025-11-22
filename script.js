document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const imageInput = document.getElementById('imageInput');
    const widthInput = document.getElementById('widthInput');
    const heightInput = document.getElementById('heightInput');
    const thresholdInput = document.getElementById('thresholdInput');
    const thresholdValue = document.getElementById('thresholdValue');
    const mirrorInput = document.getElementById('mirrorInput');
    const updateBtn = document.getElementById('updateBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    const originalCanvas = document.getElementById('originalCanvas');
    const processedCanvas = document.getElementById('processedCanvas');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const processedPlaceholder = document.getElementById('processedPlaceholder');

    const originalCtx = originalCanvas.getContext('2d');
    const processedCtx = processedCanvas.getContext('2d');

    // State
    let originalImage = null;
    let fileName = 'image.png';

    // Event Listeners
    imageInput.addEventListener('change', handleImageUpload);
    thresholdInput.addEventListener('input', (e) => {
        thresholdValue.textContent = e.target.value;
        updatePreview();
    });

    // Update preview on any change if image exists
    [widthInput, heightInput, mirrorInput].forEach(input => {
        input.addEventListener('change', () => {
            if (originalImage) updatePreview();
        });
    });

    updateBtn.addEventListener('click', () => {
        if (originalImage) updatePreview();
    });

    downloadBtn.addEventListener('click', generateAndDownload);

    // Functions
    function handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        fileName = file.name;
        const reader = new FileReader();

        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                originalImage = img;

                // Hide placeholders
                uploadPlaceholder.style.display = 'none';
                processedPlaceholder.style.display = 'none';

                // Enable download button
                downloadBtn.disabled = false;

                // Draw original image (resized to fit canvas container if needed, but keeping aspect ratio)
                // For display purposes, we limit the canvas size but keep the image data
                displayOriginalImage();

                // Trigger initial processing
                updatePreview();
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }

    function displayOriginalImage() {
        if (!originalImage) return;

        // Calculate display size (max 350x350 like in Python script)
        const MAX_SIZE = 350;
        let w = originalImage.width;
        let h = originalImage.height;

        const ratio = Math.min(MAX_SIZE / w, MAX_SIZE / h);
        const displayW = Math.floor(w * ratio);
        const displayH = Math.floor(h * ratio);

        originalCanvas.width = displayW;
        originalCanvas.height = displayH;

        originalCtx.drawImage(originalImage, 0, 0, displayW, displayH);
    }

    function updatePreview() {
        if (!originalImage) return;

        const targetWidth = parseInt(widthInput.value) || 100;
        const targetHeight = parseInt(heightInput.value) || 100;
        const threshold = parseInt(thresholdInput.value);
        const isMirrored = mirrorInput.checked;

        // 1. Resize and Process
        // Create an offscreen canvas for the actual processing resolution
        const processCanvas = document.createElement('canvas');
        processCanvas.width = targetWidth;
        processCanvas.height = targetHeight;
        const ctx = processCanvas.getContext('2d');

        // Handle Mirroring
        ctx.save();
        if (isMirrored) {
            ctx.translate(targetWidth, 0);
            ctx.scale(-1, 1);
        }
        ctx.drawImage(originalImage, 0, 0, targetWidth, targetHeight);
        ctx.restore();

        // Get pixel data
        const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight);
        const data = imageData.data;

        // Binarization
        for (let i = 0; i < data.length; i += 4) {
            // Grayscale (simple average or luminance)
            // Python PIL convert('L') uses: L = R * 299/1000 + G * 587/1000 + B * 114/1000
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;

            // Threshold
            const val = gray > threshold ? 255 : 0;

            data[i] = val;     // R
            data[i + 1] = val; // G
            data[i + 2] = val; // B
            // Alpha remains unchanged (usually 255)
        }

        ctx.putImageData(imageData, 0, 0);

        // 2. Display on Preview Canvas (scaled up to be visible)
        const MAX_SIZE = 350;
        const ratio = Math.min(MAX_SIZE / targetWidth, MAX_SIZE / targetHeight);
        const displayW = Math.floor(targetWidth * ratio);
        const displayH = Math.floor(targetHeight * ratio);

        processedCanvas.width = displayW;
        processedCanvas.height = displayH;

        // Disable smoothing for pixel art look
        processedCtx.imageSmoothingEnabled = false;
        processedCtx.drawImage(processCanvas, 0, 0, displayW, displayH);
    }

    function encodeStringToList(encodedStr) {
        if (!encodedStr) return [];
        const result = [];
        let i = 0;
        while (i < encodedStr.length) {
            const char = encodedStr[i];
            let count = 1;
            let j = i + 1;
            while (j < encodedStr.length && encodedStr[j] === char) {
                count++;
                j++;
            }
            // JS array push
            result.push(`${char}${count}`);
            i = j;
        }
        return result;
    }

    function generateAndDownload() {
        if (!originalImage) return;

        const targetWidth = parseInt(widthInput.value) || 100;
        const targetHeight = parseInt(heightInput.value) || 100;
        const threshold = parseInt(thresholdInput.value);
        const isMirrored = mirrorInput.checked;

        // Re-process to get the binary data
        const processCanvas = document.createElement('canvas');
        processCanvas.width = targetWidth;
        processCanvas.height = targetHeight;
        const ctx = processCanvas.getContext('2d');

        if (isMirrored) {
            ctx.translate(targetWidth, 0);
            ctx.scale(-1, 1);
        }
        ctx.drawImage(originalImage, 0, 0, targetWidth, targetHeight);

        const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight);
        const data = imageData.data;

        // Generate Binary Data (0 for White, 1 for Black - based on Python script logic)
        // Python: 1 if pixel <= threshold else 0
        // So Dark pixels = 1, Light pixels = 0
        const binaryData = [];

        for (let y = 0; y < targetHeight; y++) {
            const row = [];
            for (let x = 0; x < targetWidth; x++) {
                const idx = (y * targetWidth + x) * 4;
                const gray = data[idx] * 0.299 + data[idx + 1] * 0.587 + data[idx + 2] * 0.114;

                // Python logic: 1 if img_resized.getpixel((x, y)) <= threshold else 0
                // Note: getpixel returns 0-255. 
                // If pixel is dark (<= threshold), it's a 1.
                row.push(gray <= threshold ? 1 : 0);
            }
            binaryData.push(row);
        }

        // RLE Encoding
        const printCodeData = [];
        for (const row of binaryData) {
            const encodedString = row.join('');
            const printCodeRow = encodeStringToList(encodedString);
            printCodeData.push(printCodeRow);
        }

        // Format for Python file
        // We need to format the array of arrays as a Python string
        // JSON.stringify is close, but we need single quotes usually preferred in Python, 
        // though JSON (double quotes) is valid Python for lists of strings.
        // Let's stick to JSON.stringify which produces valid Python list syntax: [["110", "05"], ...]
        const printCodeString = JSON.stringify(printCodeData);
        // If we want strictly single quotes like the original might have produced (though not strictly necessary), we can replace.
        // But standard JSON is fine for Python `ast.literal_eval` or direct paste.
        // The original script used standard repr() or list str() which uses brackets.

        const fileContent = `# Generated by PrintCodeGenerator Web App
# Image: ${fileName}
# Resolution: ${targetWidth}x${targetHeight}, Threshold: ${threshold}, Mirrored: ${isMirrored}
# NOTE: 1 represents BLACK, 0 represents WHITE
print_codes = ${printCodeString}
`;

        // Create Blob and Download
        const blob = new Blob([fileContent], { type: 'text/x-python;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'image_print_codes.py';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});
