async function checkin(userId) {
    const tonConnectUI = window.tonConnectUI;
    const isConnected = await tonConnectUI.connected;
    if (!isConnected){
        try{
            await tonConnectUI.connectWallet();
        } catch (err) {
            console.error('Failed to connect wallet:', err);
            return;
        }
    }
    const body = beginCell()
        .storeUint(0, 32) // write 32 zero bits to indicate that a text comment will follow
        .storeStringTail(userId.toString())// write our text comment
        .endCell();
    const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [
            {
                address: "UQC-q-xhxis_fL8ye5iOLrlmKWMM4pufdvzsluOzLurdBgfp",
                amount: toNano("0.05").toString(),
                payload: body.toBoc().toString("base64")
            }
        ]
    };

    try {
        console.log('Sending transaction...');

        const loadingAnimation = document.querySelector('.loading-animation');
        const startBtn = document.querySelector('#task-2 .start-btn');
        // Убедитесь, что элемент найден
        if (loadingAnimation) {
            // Установите стиль display на "flex"
            loadingAnimation.style.display = 'flex';
            startBtn.style.display = 'none';
        }

        const result = await tonConnectUI.sendTransaction(transaction);
        console.log('Transaction successful:', result);

        const bocBytes = TonWeb.utils.base64ToBytes(result.boc);
        const cell = await TonWeb.boc.Cell.oneFromBoc(bocBytes);
        const hash = await cell.hash();
        const hashBase64 = TonWeb.utils.bytesToBase64(hash);
        // Отправляем данные на сервер
        const response = await fetch('/process_transaction', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userId: userId,
                msg_hash: hashBase64,
                payload: body.toBoc().toString("base64"),
                type: 'check-in'
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const activeElement = document.querySelector('.type-item.active');
            const elementId = activeElement.id;
            loadTasks(elementId);

        } else {
            const activeElement = document.querySelector('.type-item.active');
            const elementId = activeElement.id;
            loadTasks(elementId);
        }
    } catch (err) {
        const activeElement = document.querySelector('.type-item.active');
        const elementId = activeElement.id;
        loadTasks(elementId);
    }
}
