// Frontend application logic for Triola.cz AI Copywriter

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // STATE VARIABLES
    // ----------------------------------------------------
    let currentTab = 'generator';
    let selectedProduct = null;
    let generatedText = '';
    let productDatabase = []; // Cached full catalog
    let customProducts = JSON.parse(localStorage.getItem('custom_products') || '[]');

    // Initialize Lucide Icons
    lucide.createIcons();

    // Configure Markdown parser options
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // ----------------------------------------------------
    // DOM ELEMENTS
    // ----------------------------------------------------
    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const tabTitle = document.getElementById('tab-title');
    const badgeProductCount = document.getElementById('badge-product-count');

    // Status Badges
    const statusFeed = document.getElementById('status-feed');
    const statusAnthropic = document.getElementById('status-anthropic');
    const statusOpenAI = document.getElementById('status-openai');
    const statusGoogle = document.getElementById('status-google');

    // Settings tab status indicators
    const settingsCardAnthropic = document.getElementById('settings-card-anthropic');
    const settingsCardOpenAI = document.getElementById('settings-card-openai');
    const settingsCardGoogle = document.getElementById('settings-card-google');
    const settingsProductCount = document.getElementById('settings-product-count');

    // Tab 1: Generator
    const searchProductInput = document.getElementById('search-product-input');
    const clearSearchBtn = document.getElementById('clear-search-btn');
    const searchResultsDropdown = document.getElementById('search-autocomplete-results');
    const selectedProductCard = document.getElementById('selected-product-card');
    const removeProductBtn = document.getElementById('remove-product-btn');
    const noProductAlert = document.getElementById('no-product-alert');
    
    // Selected Product Details in Card
    const productCutBadge = document.getElementById('product-cut-badge');
    const productCardTitle = document.getElementById('product-card-title');
    const productCardCode = document.getElementById('product-card-code');
    const productCardPrice = document.getElementById('product-card-price');
    const productCardColors = document.getElementById('product-card-colors');
    const productCardDescText = document.getElementById('product-card-desc-text');

    // Generator Options
    const formatSelect = document.getElementById('format-select');
    const modelSelect = document.getElementById('model-select');
    const toneSelect = document.getElementById('tone-select');
    const lengthSelect = document.getElementById('length-select');
    const keywordsInput = document.getElementById('keywords-input');
    const instructionsTextarea = document.getElementById('instructions-textarea');
    const generateBtn = document.getElementById('generate-btn');

    // Generator Output Panels
    const modeTabs = document.querySelectorAll('.mode-tab');
    const outputViewRendered = document.getElementById('output-view-rendered');
    const outputViewEditor = document.getElementById('output-view-editor');
    const outputViewRaw = document.getElementById('output-view-raw');
    const outputTextarea = document.getElementById('output-textarea');
    const outputMarkdownCode = document.getElementById('output-markdown-code');
    const generationLoader = document.getElementById('generation-loader');
    const loaderStatusText = document.getElementById('loader-status-text');

    // Footer actions
    const copyClipboardBtn = document.getElementById('copy-clipboard-btn');
    const downloadMdBtn = document.getElementById('download-md-btn');
    const downloadHtmlBtn = document.getElementById('download-html-btn');
    const textStats = document.getElementById('text-stats');
    const wordCount = document.getElementById('word-count');
    const charCount = document.getElementById('char-count');

    // Tab 2: Catalog
    const catalogSearchInput = document.getElementById('catalog-search-input');
    const catalogTableBody = document.getElementById('catalog-table-body');
    const addManualProductBtn = document.getElementById('add-manual-product-btn');

    // Tab 4: Settings
    const updateFeedBtn = document.getElementById('update-feed-btn');

    // Modal
    const manualProductModal = document.getElementById('manual-product-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const manualProductForm = document.getElementById('manual-product-form');

    // ----------------------------------------------------
    // INITIALIZATION & CHECKS
    // ----------------------------------------------------
    updateAppStatus();
    loadCatalog();

    // ----------------------------------------------------
    // NAVIGATION LOGIC
    // ----------------------------------------------------
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    function switchTab(tabId) {
        currentTab = tabId;
        
        // Update nav items
        navItems.forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update tab content
        tabPanes.forEach(pane => {
            if (pane.id === `tab-${tabId}`) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // Update Header Title
        const titleMapping = {
            generator: 'Generátor textů',
            catalog: 'Knihovna modelů Triola',
            batch: 'Hromadné generování z Excelu',
            seo: 'Prediktivně kalibrované SEO snippety',
            brandbook: 'Triola Brand Book & Stylistika',
            settings: 'Nastavení systému & API'
        };
        tabTitle.textContent = titleMapping[tabId] || 'Rozhraní';
        
        // Special actions on tab loading
        if (tabId === 'catalog') {
            renderCatalogTable(productDatabase);
        }
    }

    // ----------------------------------------------------
    // API & STATUS LOGIC
    // ----------------------------------------------------
    async function updateAppStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update XML Feed status badge
            if (data.product_count > 0) {
                updateDotStatus(statusFeed, 'green', `XML Feed: ${data.product_count} produktů`);
                badgeProductCount.textContent = data.product_count;
                settingsProductCount.textContent = data.product_count;
            } else {
                updateDotStatus(statusFeed, 'yellow', 'XML Feed: Prázdný');
            }

            // Update Excel status badge
            const statusExcel = document.getElementById('status-excel');
            const settingsMarketingCount = document.getElementById('settings-marketing-count');
            if (data.excel_present && data.marketing_count > 0) {
                updateDotStatus(statusExcel, 'green', `Excel podklady: ${data.marketing_count} modelů`);
                if (settingsMarketingCount) settingsMarketingCount.textContent = data.marketing_count;
            } else {
                updateDotStatus(statusExcel, 'red', 'Excel podklady: Chybí');
                if (settingsMarketingCount) settingsMarketingCount.textContent = '0';
            }

            // Update LLM keys status badges
            updateKeyStatus(statusAnthropic, settingsCardAnthropic, data.anthropic_key, "Claude API");
            updateKeyStatus(statusOpenAI, settingsCardOpenAI, data.openai_key, "GPT-4o API");
            updateKeyStatus(statusGoogle, settingsCardGoogle, data.google_key, "Gemini API");
        } catch (e) {
            console.error("Chyba při zjišťování stavu aplikace:", e);
        }
    }

    function updateDotStatus(element, color, text) {
        if (!element) return;
        const dot = element.querySelector('.dot');
        const span = element.querySelector('span:not(.dot)');
        
        // Remove old classes
        dot.className = 'dot ' + color;
        span.textContent = text;
    }

    function updateKeyStatus(sidebarElement, settingsCard, isAvailable, name) {
        // Sidebar element
        if (sidebarElement) {
            const color = isAvailable ? 'green' : 'red';
            updateDotStatus(sidebarElement, color, `${name}: ${isAvailable ? 'Aktivní' : 'Nenastaveno'}`);
        }
        
        // Settings page card
        if (settingsCard) {
            const badge = settingsCard.querySelector('.api-badge');
            if (isAvailable) {
                badge.className = 'api-badge status-connected';
                badge.innerHTML = '<i data-lucide="check-circle-2"></i> Aktivní';
            } else {
                badge.className = 'api-badge status-disconnected';
                badge.innerHTML = '<i data-lucide="circle-alert"></i> Nenastaveno v .env';
            }
            lucide.createIcons({ attrs: { class: 'lucide-icon' } });
        }
    }

    // ----------------------------------------------------
    // SEARCH & AUTOCOMPLETE LOGIC (GENERATOR)
    // ----------------------------------------------------
    let autocompleteTimeout = null;

    searchProductInput.addEventListener('input', () => {
        const query = searchProductInput.value.trim();
        
        if (query.length > 0) {
            clearSearchBtn.style.display = 'flex';
        } else {
            clearSearchBtn.style.display = 'none';
        }

        clearTimeout(autocompleteTimeout);
        if (query.length < 2) {
            searchResultsDropdown.style.display = 'none';
            return;
        }

        autocompleteTimeout = setTimeout(async () => {
            try {
                // Search both feed products and manual custom products
                const response = await fetch(`/api/products?q=${encodeURIComponent(query)}`);
                const products = await response.json();
                
                // Add matching custom products
                const customMatches = customProducts.filter(p => 
                    p.model_code.toLowerCase().includes(query.toLowerCase()) || 
                    p.generic_title.toLowerCase().includes(query.toLowerCase()) ||
                    p.cut_name.toLowerCase().includes(query.toLowerCase())
                );
                
                // Merge lists (avoiding duplicates)
                const mergedProducts = [...customMatches];
                products.forEach(p => {
                    if (!mergedProducts.some(mp => mp.model_code === p.model_code)) {
                        mergedProducts.push(p);
                    }
                });

                showAutocompleteDropdown(mergedProducts.slice(0, 10));
            } catch (e) {
                console.error("Chyba při vyhledávání produktů:", e);
            }
        }, 150);
    });

    clearSearchBtn.addEventListener('click', () => {
        searchProductInput.value = '';
        clearSearchBtn.style.display = 'none';
        searchResultsDropdown.style.display = 'none';
        searchProductInput.focus();
    });

    // Close autocomplete on click outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-box-container')) {
            searchResultsDropdown.style.display = 'none';
        }
    });

    function showAutocompleteDropdown(items) {
        if (items.length === 0) {
            searchResultsDropdown.innerHTML = '<div style="padding: 12px 16px; font-size: 13px; color: var(--text-muted);">Nebyly nalezeny žádné odpovídající střihy ani modely...</div>';
            searchResultsDropdown.style.display = 'block';
            return;
        }

        searchResultsDropdown.innerHTML = '';
        items.forEach(p => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            
            // Build item markup
            const isCustom = customProducts.some(cp => cp.model_code === p.model_code);
            const badgeHtml = isCustom ? '<span style="color: var(--gold); font-size: 10px; font-weight:700; border: 1px solid var(--gold); padding: 1px 4px; border-radius:3px;">Ručně přidaný</span>' : '';
            
            div.innerHTML = `
                <div class="item-title">${p.generic_title} ${badgeHtml}</div>
                <div class="item-meta">
                    <span>Kód: <strong>${p.model_code}</strong></span>
                    <span>Střih: <strong>${p.cut_name}</strong></span>
                    <span>Barvy: ${p.all_colors.slice(0, 3).join(', ')}${p.all_colors.length > 3 ? '...' : ''}</span>
                </div>
            `;
            
            div.addEventListener('click', () => {
                selectProduct(p);
                searchResultsDropdown.style.display = 'none';
            });
            searchResultsDropdown.appendChild(div);
        });
        searchResultsDropdown.style.display = 'block';
    }

    function selectProduct(product) {
        selectedProduct = product;
        searchProductInput.value = `${product.generic_title} (${product.model_code})`;
        clearSearchBtn.style.display = 'flex';
        
        // Update product summary card details
        productCutBadge.textContent = product.cut_name;
        
        // Cut badges colors
        const cutClass = product.cut_name.toLowerCase().replace(/\s/g, '-');
        productCutBadge.className = `product-badge ${cutClass}`;
        
        productCardTitle.textContent = product.generic_title;
        productCardCode.textContent = product.model_code;
        productCardPrice.textContent = product.base_price ? product.base_price : 'Cena na dotaz';
        
        // Colors
        productCardColors.innerHTML = '';
        product.all_colors.forEach(c => {
            const span = document.createElement('span');
            span.className = 'color-tag';
            span.textContent = c;
            productCardColors.appendChild(span);
        });

        // Description
        productCardDescText.textContent = product.combined_description || 'Pro tento produkt není v XML feedu uveden žádný popisek.';
        
        // Marketing Data Preview
        const productCardMarketing = document.getElementById('product-card-marketing');
        const productCardCollection = document.getElementById('product-card-collection');
        const productCardTarget = document.getElementById('product-card-target');
        const productCardArgs = document.getElementById('product-card-args');

        if (product.collection || product.sales_arguments || product.target_group) {
            productCardCollection.textContent = product.collection || 'neuvedena';
            productCardTarget.textContent = product.target_group || 'neuvedena';
            // Parse arguments newlines to bullet list or text
            const argsText = product.sales_arguments ? product.sales_arguments.replace(/\\n/g, '<br>').replace(/- /g, '• ') : 'neuvedeny';
            productCardArgs.innerHTML = argsText;
            productCardMarketing.style.display = 'block';
        } else {
            productCardMarketing.style.display = 'none';
        }
        
        // Show card and hide alert
        selectedProductCard.style.display = 'block';
        noProductAlert.style.display = 'none';
        
        // Pre-fill model code in search input for ease
        loggingActivity(`Vybrán produkt kód: ${product.model_code}`);
    }

    removeProductBtn.addEventListener('click', () => {
        selectedProduct = null;
        searchProductInput.value = '';
        clearSearchBtn.style.display = 'none';
        selectedProductCard.style.display = 'none';
        noProductAlert.style.display = 'flex';
    });

    // ----------------------------------------------------
    // GENERATION LOGIC
    // ----------------------------------------------------
    generateBtn.addEventListener('click', async () => {
        const format = formatSelect.value;
        const model = modelSelect.value;
        const tone = toneSelect.value;
        const length = lengthSelect.value;
        const keywords = keywordsInput.value.trim();
        const customInstructions = instructionsTextarea.value.trim();

        // Prepare request body
        const requestData = {
            format_type: format,
            model_key: model,
            tone_key: tone,
            length_key: length,
            keywords: keywords,
            custom_instructions: customInstructions,
            use_simulation: (model === 'simulation')
        };

        if (selectedProduct) {
            requestData.product_code = selectedProduct.model_code;
        } else {
            // Require user to select a product unless they explicitly want general guidelines
            const code = prompt("Nezadali jste produkt. Pokud chcete generovat texty pro konkrétní kód modelu (např. 28746), napište ho sem, nebo nechte prázdné pro obecný text o značce Triola:");
            if (code === null) return; // User cancelled
            requestData.product_code = code.trim();
        }

        // Show Loader
        generationLoader.style.display = 'flex';
        generateBtn.disabled = true;
        
        // Set funny writing statements
        const writingMessages = [
            "AI asistent analyzuje střihové vlastnosti Trioly...",
            "Sestavuji brafitting pravidla z Brand Booku...",
            "Ladím češtinu pro co nejpřirozenější čtení...",
            "Formuluji přesvědčivý a čtivý text...",
            "Finální stylistická kontrola textu..."
        ];
        
        let messageIdx = 0;
        loaderStatusText.textContent = writingMessages[messageIdx];
        const statusTimer = setInterval(() => {
            messageIdx = (messageIdx + 1) % writingMessages.length;
            loaderStatusText.textContent = writingMessages[messageIdx];
        }, 3000);

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            clearInterval(statusTimer);

            if (result.success) {
                generatedText = result.text;
                
                // Show result in all tabs
                updateGeneratedOutput(generatedText);
                loggingActivity(`Úspěšně vygenerován text formátu ${format} pomocí ${model}`);
            } else {
                showGenerationError(result.error || "Při volání API došlo k chybě.");
            }
        } catch (e) {
            clearInterval(statusTimer);
            showGenerationError(e.message || "Nepodařilo se navázat spojení se serverem.");
        } finally {
            generationLoader.style.display = 'none';
            generateBtn.disabled = false;
        }
    });

    function updateGeneratedOutput(text) {
        // Render markdown
        outputViewRendered.innerHTML = marked.parse(text);
        
        // Update raw markdown code view
        outputMarkdownCode.textContent = text;
        
        // Fill editor text area
        outputTextarea.value = text;

        // Statistics
        const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
        const chars = text.length;
        wordCount.textContent = words;
        charCount.textContent = chars;
        textStats.style.display = 'block';

        // Enable download buttons
        downloadMdBtn.disabled = false;
        downloadHtmlBtn.disabled = false;

        // Set Rendered view active by default
        switchOutputMode('rendered');
    }

    function showGenerationError(errorMsg) {
        outputViewRendered.innerHTML = `
            <div class="rule-card danger" style="margin: 20px;">
                <h3><i data-lucide="circle-alert"></i> Chyba při generování</h3>
                <p>Omlouváme se, ale text se nepodařilo vytvořit. Důvod:</p>
                <code style="background-color: #fcebeb; padding: 10px; border-radius: 6px; display: block; margin: 10px 0; color: var(--danger); font-size:12.5px; border: 1px solid #f8d7da;">${errorMsg}</code>
                <p style="font-size: 13px; margin-top: 10px;">Zkontrolujte prosím své nastavení API klíčů v souboru <code>.env</code> a ověřte připojení k internetu.</p>
            </div>
        `;
        // Enable switch tab to see error clearly
        switchOutputMode('rendered');
        
        // Disable action buttons
        downloadMdBtn.disabled = true;
        downloadHtmlBtn.disabled = true;
        textStats.style.display = 'none';
        lucide.createIcons();
    }

    // ----------------------------------------------------
    // OUTPUT VIEW SWITCHING
    // ----------------------------------------------------
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.getAttribute('data-mode');
            switchOutputMode(mode);
        });
    });

    function switchOutputMode(mode) {
        // Update active class on tabs
        modeTabs.forEach(t => {
            if (t.getAttribute('data-mode') === mode) {
                t.classList.add('active');
            } else {
                t.classList.remove('active');
            }
        });

        // Hide all panes
        outputViewRendered.classList.remove('active');
        outputViewEditor.classList.remove('active');
        outputViewRaw.classList.remove('active');

        // Show selected pane
        if (mode === 'rendered') {
            // Re-render editor changes back to preview
            outputViewRendered.innerHTML = marked.parse(outputTextarea.value);
            outputViewRendered.classList.add('active');
        } else if (mode === 'editor') {
            outputViewEditor.classList.add('active');
            outputTextarea.focus();
        } else if (mode === 'raw') {
            outputMarkdownCode.textContent = outputTextarea.value;
            outputViewRaw.classList.add('active');
        }
    }

    // Sync Stats on direct edit in editor
    outputTextarea.addEventListener('input', () => {
        const text = outputTextarea.value;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
        const chars = text.length;
        wordCount.textContent = words;
        charCount.textContent = chars;
    });

    // ----------------------------------------------------
    // COPY TO CLIPBOARD
    // ----------------------------------------------------
    copyClipboardBtn.addEventListener('click', () => {
        const textToCopy = outputTextarea.value;
        if (!textToCopy) return;

        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalHtml = copyClipboardBtn.innerHTML;
            copyClipboardBtn.innerHTML = '<i data-lucide="check" style="color: var(--success)"></i><span style="color: var(--success)">Zkopírováno!</span>';
            lucide.createIcons({ attrs: { class: 'lucide-icon' } });
            
            setTimeout(() => {
                copyClipboardBtn.innerHTML = originalHtml;
                lucide.createIcons({ attrs: { class: 'lucide-icon' } });
            }, 2000);
        });
    });

    // ----------------------------------------------------
    // FILE DOWNLOAD ACTIONS
    // ----------------------------------------------------
    downloadMdBtn.addEventListener('click', () => {
        const text = outputTextarea.value;
        if (!text) return;
        
        let filename = 'triola-text.md';
        if (selectedProduct) {
            filename = `triola-kody-${selectedProduct.model_code}-${formatSelect.value}.md`;
        }
        
        downloadFile(text, filename, 'text/markdown;charset=utf-8;');
    });

    downloadHtmlBtn.addEventListener('click', () => {
        const rawText = outputTextarea.value;
        if (!rawText) return;
        
        const htmlContent = `
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>Triola Copywriting AI Export</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #222; }
        h1, h2, h3 { color: #8C1D31; }
        h1 { border-bottom: 1px solid #E8DFD8; padding-bottom: 8px; }
        ul, ol { margin-left: 20px; }
        li { margin-bottom: 6px; }
        blockquote { border-left: 4px solid #8C1D31; padding-left: 16px; margin: 20px 0; color: #555; font-style: italic; }
    </style>
</head>
<body>
    ${marked.parse(rawText)}
</body>
</html>`;

        let filename = 'triola-text.html';
        if (selectedProduct) {
            filename = `triola-kody-${selectedProduct.model_code}-${formatSelect.value}.html`;
        }
        
        downloadFile(htmlContent, filename, 'text/html;charset=utf-8;');
    });

    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ----------------------------------------------------
    // KNOHOVNA / CATALOG LOGIC
    // ----------------------------------------------------
    async function loadCatalog() {
        try {
            const response = await fetch('/api/products?all=true');
            productDatabase = await response.json();
            
            // Re-render count
            badgeProductCount.textContent = productDatabase.length;
            settingsProductCount.textContent = productDatabase.length;
            
            if (currentTab === 'catalog') {
                renderCatalogTable(productDatabase);
            }
        } catch (e) {
            console.error("Chyba při stahování katalogu produktů:", e);
        }
    }

    function renderCatalogTable(items) {
        catalogTableBody.innerHTML = '';
        
        // Merge feed items and custom products (custom items first)
        const combined = [...customProducts];
        items.forEach(item => {
            if (!combined.some(c => c.model_code === item.model_code)) {
                combined.push(item);
            }
        });

        if (combined.length === 0) {
            catalogTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Knihovna neobsahuje žádné modely. Aktualizujte XML feed.</td></tr>';
            return;
        }

        combined.forEach(p => {
            const tr = document.createElement('tr');
            
            const isCustom = customProducts.some(cp => cp.model_code === p.model_code);
            const badgeClass = p.cut_name.toLowerCase().replace(/\s/g, '-');
            const customTagHtml = isCustom ? '<span style="color: var(--gold); border: 1px solid var(--gold); padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight:700; margin-left:6px; display:inline-block; line-height:1;">Custom</span>' : '';
            
            tr.innerHTML = `
                <td class="model-code-cell">${p.model_code}</td>
                <td class="title-cell">${p.generic_title} ${customTagHtml}</td>
                <td>${p.brand}</td>
                <td class="badge-cell"><span class="${badgeClass}">${p.cut_name}</span></td>
                <td>${p.all_colors.join(', ')}</td>
                <td>${p.base_price ? p.base_price : 'Cena na dotaz'}</td>
                <td class="action-cell">
                    <button class="btn secondary-btn select-from-catalog-btn" data-code="${p.model_code}" style="padding: 6px 12px; font-size:12px;">
                        <i data-lucide="check" style="width:13px; height:13px; display:inline-block; vertical-align:middle; margin-right:4px;"></i> Zvolit k psaní
                    </button>
                </td>
            `;
            
            // Select button handler
            tr.querySelector('.select-from-catalog-btn').addEventListener('click', () => {
                selectProduct(p);
                switchTab('generator');
            });

            catalogTableBody.appendChild(tr);
        });
        
        lucide.createIcons();
    }

    // Catalog search
    catalogSearchInput.addEventListener('input', () => {
        const query = catalogSearchInput.value.toLowerCase().trim();
        
        const filtered = productDatabase.filter(p => {
            return (
                p.model_code.toLowerCase().includes(query) ||
                p.generic_title.toLowerCase().includes(query) ||
                p.cut_name.toLowerCase().includes(query) ||
                p.brand.toLowerCase().includes(query) ||
                p.all_colors.some(c => c.toLowerCase().includes(query))
            );
        });
        
        renderCatalogTable(filtered);
    });

    // ----------------------------------------------------
    // MANUAL CUSTOM PRODUCT MODAL LOGIC
    // ----------------------------------------------------
    addManualProductBtn.addEventListener('click', () => {
        manualProductModal.style.display = 'flex';
        document.getElementById('modal-code').focus();
    });

    closeModalBtn.addEventListener('click', closeModal);
    manualProductModal.addEventListener('click', (e) => {
        if (e.target === manualProductModal) {
            closeModal();
        }
    });

    function closeModal() {
        manualProductModal.style.display = 'none';
        manualProductForm.reset();
    }

    manualProductForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const code = document.getElementById('modal-code').value.trim();
        const title = document.getElementById('modal-title').value.trim();
        const cut = document.getElementById('modal-cut').value;
        const price = document.getElementById('modal-price').value.trim();
        const colorsInput = document.getElementById('modal-colors').value.trim();
        const desc = document.getElementById('modal-desc').value.trim();

        // Process colors
        const colors = colorsInput ? colorsInput.split(',').map(c => c.trim()).filter(c => c.length > 0) : ['standardní'];

        // Determine properties of cut
        let characteristics = "Ručně definovaný vlastní model.";
        let benefits = [];
        
        // Auto benefit loading if cut is standard
        if (cut === 'Perfect-Fit') {
            characteristics = "Hladká, tence vyztužená podprsenka s kosticemi navržená pro maximální oporu a formování postavy.";
            benefits = ["Tence vyztužené bezešvé košíčky", "Flexi kostice se přizpůsobí pohybu těla", "Rozšířená ramínka ulevují ramenům"];
        } else if (cut === 'T-Fit') {
            characteristics = "Tradiční vyztužený střih s třídílnými košíčky sešitými do tvaru písmene T.";
            benefits = ["Třídílný šitý košíček prsa perfektně zakulatí", "Pevné kostice pro spolehlivou oporu"];
        }

        const newProduct = {
            model_code: code,
            generic_title: title,
            brand: "Triola",
            type: "Dámské spodní prádlo",
            cut_name: cut,
            characteristics: characteristics,
            benefits: benefits,
            base_price: price || 'Cena na dotaz',
            all_colors: colors,
            combined_description: desc
        };

        // Add to local state list
        // Replace if already exists in custom list
        const existingIdx = customProducts.findIndex(p => p.model_code === code);
        if (existingIdx >= 0) {
            customProducts[existingIdx] = newProduct;
        } else {
            customProducts.unshift(newProduct);
        }

        // Save to localStorage
        localStorage.setItem('custom_products', JSON.stringify(customProducts));
        
        closeModal();
        loadCatalog(); // Reload database
        
        // Automatically select the new manual product
        selectProduct(newProduct);
        switchTab('generator');
        
        alert(`Model ${code} byl úspěšně uložen a aktivován do generátoru.`);
    });

    // ----------------------------------------------------
    // FEED UPDATE LOGIC (SETTINGS)
    // ----------------------------------------------------
    updateFeedBtn.addEventListener('click', async () => {
        updateFeedBtn.disabled = true;
        const originalText = updateFeedBtn.innerHTML;
        updateFeedBtn.innerHTML = '<i data-lucide="refresh-cw" class="spin"></i> <span>Aktualizuji feed...</span>';
        lucide.createIcons();

        try {
            const response = await fetch('/api/feed/update', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                alert(`Feed a marketingová data úspěšně aktualizována! (E-shop: ${data.product_count} modelů, Excel: ${data.marketing_count} modelů)`);
                updateAppStatus();
                loadCatalog();
            } else {
                alert(`Chyba při stahování XML feedu: ${data.error}`);
            }
        } catch (e) {
            alert(`Chyba připojení: ${e.message}`);
        } finally {
            updateFeedBtn.innerHTML = originalText;
            updateFeedBtn.disabled = false;
            lucide.createIcons();
        }
    });

    // Logger logger console output
    function loggingActivity(msg) {
        console.log(`[Triola Copywriter] ${new Date().toLocaleTimeString()}: ${msg}`);
    }

    // ----------------------------------------------------
    // TAB 5: BATCH PROCESSING LOGIC
    // ----------------------------------------------------
    let batchFilename = '';
    let batchRows = [];
    let batchIsProcessing = false;
    let batchCancelRequested = false;

    // DOM Elements for Batch tab
    const batchUploadArea = document.getElementById('batch-upload-area');
    const batchFileInput = document.getElementById('batch-file-input');
    const batchUploadLink = document.getElementById('batch-upload-link');
    const batchFileSummary = document.getElementById('batch-file-summary');
    const batchFilenameEl = document.getElementById('batch-filename');
    const batchRowsCountEl = document.getElementById('batch-rows-count');
    const batchRemoveFileBtn = document.getElementById('batch-remove-file-btn');
    const batchModelSelect = document.getElementById('batch-model-select');
    const batchToneSelect = document.getElementById('batch-tone-select');
    const batchSimulateCheckbox = document.getElementById('batch-simulate-checkbox');
    const batchStartBtn = document.getElementById('batch-start-btn');
    const batchDownloadBtn = document.getElementById('batch-download-btn');
    const batchProgressPanel = document.getElementById('batch-progress-panel');
    const batchProgressText = document.getElementById('batch-progress-text');
    const batchProgressBar = document.getElementById('batch-progress-bar');
    const batchTableBody = document.getElementById('batch-table-body');
    const batchPreviewModal = document.getElementById('batch-preview-modal');
    const closeBatchPreviewBtn = document.getElementById('close-batch-preview-btn');
    
    // Preview values
    const batchPreviewTitle = document.getElementById('batch-preview-title');
    const batchPreviewShortCode = document.getElementById('batch-preview-short-code');
    const batchPreviewShortRender = document.getElementById('batch-preview-short-render');
    const batchPreviewLongCode = document.getElementById('batch-preview-long-code');
    const batchPreviewLongRender = document.getElementById('batch-preview-long-render');

    // Trigger file input click
    if (batchUploadLink) {
        batchUploadLink.addEventListener('click', (e) => {
            e.stopPropagation();
            batchFileInput.click();
        });
    }

    if (batchUploadArea) {
        batchUploadArea.addEventListener('click', (e) => {
            if (e.target !== batchUploadLink) {
                batchFileInput.click();
            }
        });

        // Drag-and-drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            batchUploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchUploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            batchUploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchUploadArea.classList.remove('dragover');
            }, false);
        });

        batchUploadArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleBatchUpload(files[0]);
            }
        });
    }

    if (batchFileInput) {
        batchFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleBatchUpload(e.target.files[0]);
            }
        });
    }

    if (batchRemoveFileBtn) {
        batchRemoveFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            resetBatchState();
        });
    }

    function resetBatchState() {
        if (batchFileInput) batchFileInput.value = '';
        batchFilename = '';
        batchRows = [];
        batchIsProcessing = false;
        batchCancelRequested = false;
        
        if (batchFileSummary) batchFileSummary.style.display = 'none';
        if (batchUploadArea) batchUploadArea.style.display = 'block';
        if (batchStartBtn) {
            batchStartBtn.disabled = true;
            batchStartBtn.innerHTML = '<i data-lucide="play"></i> <span>Spustit hromadné generování</span>';
            batchStartBtn.className = 'btn primary-btn';
        }
        if (batchDownloadBtn) batchDownloadBtn.disabled = true;
        if (batchProgressPanel) batchProgressPanel.style.display = 'none';
        if (batchTableBody) batchTableBody.innerHTML = '';
        if (batchProgressBar) batchProgressBar.style.width = '0%';
        if (batchProgressText) batchProgressText.textContent = 'Zpracováno 0 z 0';
        lucide.createIcons();
    }

    async function handleBatchUpload(file) {
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            alert('Nahrajte prosím platný soubor typu Excel (.xlsx nebo .xls).');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        
        if (batchUploadArea) batchUploadArea.style.display = 'none';
        if (batchFileSummary) batchFileSummary.style.display = 'flex';
        if (batchFilenameEl) batchFilenameEl.textContent = 'Odesílám a analyzuji soubor...';
        if (batchRowsCountEl) batchRowsCountEl.textContent = '';
        if (batchRemoveFileBtn) batchRemoveFileBtn.disabled = true;

        try {
            const response = await fetch('/api/batch/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                batchFilename = data.filename;
                batchRows = data.rows;
                
                if (batchFilenameEl) batchFilenameEl.textContent = file.name;
                if (batchRowsCountEl) batchRowsCountEl.textContent = `Celkem ${data.total_rows} položek nalezeno k zpracování`;
                
                if (batchStartBtn) batchStartBtn.disabled = false;
                if (batchRemoveFileBtn) batchRemoveFileBtn.disabled = false;
                
                renderBatchTableRows(batchRows);
                if (batchProgressPanel) batchProgressPanel.style.display = 'block';
                if (batchProgressText) batchProgressText.textContent = `Připraveno: 0 z ${batchRows.length}`;
                if (batchProgressBar) batchProgressBar.style.width = '0%';
            } else {
                alert(`Chyba při zpracování Excelu: ${data.error}`);
                resetBatchState();
            }
        } catch (e) {
            alert(`Chyba připojení k serveru: ${e.message}`);
            resetBatchState();
        }
    }

    function renderBatchTableRows(rows) {
        if (!batchTableBody) return;
        batchTableBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.id = `batch-row-${row.row_num}`;
            tr.style.borderBottom = '1px solid var(--border-color)';
            tr.innerHTML = `
                <td style="padding: 10px; font-weight: 600;">${row.row_num}</td>
                <td style="padding: 10px; font-weight: bold; color: var(--primary);">${row.raw_code}</td>
                <td style="padding: 10px;">${row.color_name}</td>
                <td style="padding: 10px;">
                    <span class="batch-status-badge pending" id="row-badge-${row.row_num}">Čeká</span>
                </td>
                <td style="padding: 10px; text-align: right;">
                    <button type="button" class="batch-preview-btn" id="preview-btn-${row.row_num}" disabled>
                        <i data-lucide="eye" style="width:14px; height:14px; display:inline-block; vertical-align:middle; margin-right:4px;"></i>
                        <span>Náhled</span>
                    </button>
                </td>
            `;
            batchTableBody.appendChild(tr);
        });
        lucide.createIcons();
    }

    // Start batch execution loop
    if (batchStartBtn) {
        batchStartBtn.addEventListener('click', async () => {
            if (batchIsProcessing) {
                batchCancelRequested = true;
                batchStartBtn.innerHTML = '<i data-lucide="square"></i> <span>Ruším...</span>';
                batchStartBtn.disabled = true;
                lucide.createIcons();
                return;
            }

            batchIsProcessing = true;
            batchCancelRequested = false;
            batchStartBtn.innerHTML = '<i data-lucide="square"></i> <span>Zrušit generování</span>';
            batchStartBtn.className = 'btn danger-btn';
            if (batchRemoveFileBtn) batchRemoveFileBtn.disabled = true;
            if (batchDownloadBtn) batchDownloadBtn.disabled = true;
            lucide.createIcons();
            
            let processed = 0;
            const total = batchRows.length;
            const model_key = batchModelSelect ? batchModelSelect.value : 'claude-sonnet-4-6';
            const tone_key = batchToneSelect ? batchToneSelect.value : 'empaticky';
            const use_simulation = batchSimulateCheckbox ? batchSimulateCheckbox.checked : false;

            for (let i = 0; i < total; i++) {
                if (batchCancelRequested) {
                    break;
                }

                const row = batchRows[i];
                const badge = document.getElementById(`row-badge-${row.row_num}`);
                if (badge) {
                    badge.className = 'batch-status-badge processing';
                    badge.textContent = 'Generuji';
                }
                
                const tr = document.getElementById(`batch-row-${row.row_num}`);
                if (tr) {
                    tr.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                try {
                    const response = await fetch('/api/batch/process-row', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            filename: batchFilename,
                            row_num: row.row_num,
                            model_code: row.model_code,
                            color_name: row.color_name,
                            arguments: row.arguments,
                            model_key: model_key,
                            tone_key: tone_key,
                            use_simulation: use_simulation
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        if (badge) {
                            badge.className = 'batch-status-badge success';
                            badge.textContent = 'Hotovo';
                        }
                        
                        const previewBtn = document.getElementById(`preview-btn-${row.row_num}`);
                        if (previewBtn) {
                            previewBtn.disabled = false;
                            previewBtn.setAttribute('data-short-html', data.short_desc);
                            previewBtn.setAttribute('data-long-html', data.long_desc);
                            previewBtn.setAttribute('data-code', row.raw_code);
                            
                            previewBtn.onclick = () => {
                                showBatchPreview(row.raw_code, data.short_desc, data.long_desc);
                            };
                        }
                    } else {
                        if (badge) {
                            badge.className = 'batch-status-badge error';
                            badge.textContent = 'Chyba';
                        }
                        console.error(`Chyba zpracování řádku ${row.row_num}: ${data.error}`);
                    }
                } catch (err) {
                    if (badge) {
                        badge.className = 'batch-status-badge error';
                        badge.textContent = 'Chyba';
                    }
                    console.error(`Chyba připojení na řádku ${row.row_num}:`, err);
                }
                
                processed++;
                if (batchProgressText) batchProgressText.textContent = `Zpracováno ${processed} z ${total}`;
                if (batchProgressBar) batchProgressBar.style.width = `${(processed / total) * 100}%`;

                // Wait 1.5 seconds before processing the next row to prevent API rate limits / overloading
                if (i < total - 1 && !batchCancelRequested) {
                    await new Promise(resolve => setTimeout(resolve, 1500));
                }
            }

            // Reset UI state
            batchIsProcessing = false;
            batchStartBtn.innerHTML = '<i data-lucide="play"></i> <span>Spustit hromadné generování</span>';
            batchStartBtn.className = 'btn primary-btn';
            batchStartBtn.disabled = false;
            if (batchRemoveFileBtn) batchRemoveFileBtn.disabled = false;
            if (batchDownloadBtn) batchDownloadBtn.disabled = false;
            lucide.createIcons();

            if (batchCancelRequested) {
                alert('Hromadné generování bylo zrušeno uživatelem.');
                batchCancelRequested = false;
            } else {
                alert('Hromadné generování bylo úspěšně dokončeno! Nyní si můžete stáhnout upravenou tabulku.');
            }
        });
    }

    // Preview modal handlers
    function showBatchPreview(code, shortHtml, longHtml) {
        if (batchPreviewTitle) batchPreviewTitle.textContent = `Náhled popisků pro model: ${code}`;
        
        if (batchPreviewShortCode) batchPreviewShortCode.textContent = shortHtml;
        if (batchPreviewShortRender) batchPreviewShortRender.innerHTML = shortHtml;
        
        if (batchPreviewLongCode) batchPreviewLongCode.textContent = longHtml;
        if (batchPreviewLongRender) batchPreviewLongRender.innerHTML = longHtml;
        
        if (batchPreviewModal) batchPreviewModal.style.display = 'flex';
    }

    if (closeBatchPreviewBtn) {
        closeBatchPreviewBtn.addEventListener('click', () => {
            if (batchPreviewModal) batchPreviewModal.style.display = 'none';
        });
    }

    // Close on overlay click
    if (batchPreviewModal) {
        batchPreviewModal.addEventListener('click', (e) => {
            if (e.target === batchPreviewModal) {
                batchPreviewModal.style.display = 'none';
            }
        });
    }

    // Download generated Excel
    if (batchDownloadBtn) {
        batchDownloadBtn.addEventListener('click', () => {
            if (!batchFilename) return;
            window.location.href = `/api/batch/download/${batchFilename}`;
        });
    }

    // ----------------------------------------------------
    // TAB 6: SEO SNIPPETS LOGIC
    // ----------------------------------------------------
    // Inner subpane switching
    const seoTabBtns = document.querySelectorAll('.seo-tab-btn');
    const seoSubpanes = document.querySelectorAll('.seo-subpane');

    seoTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-seo-mode');
            
            // Toggle buttons
            seoTabBtns.forEach(b => {
                if (b.getAttribute('data-seo-mode') === mode) {
                    b.classList.add('active');
                    b.style.color = 'var(--primary)';
                    b.style.borderBottom = '2px solid var(--primary)';
                } else {
                    b.classList.remove('active');
                    b.style.color = 'var(--text-muted)';
                    b.style.borderBottom = 'none';
                }
            });

            // Toggle panes
            seoSubpanes.forEach(pane => {
                if (pane.id === `seo-pane-${mode}`) {
                    pane.classList.add('active');
                } else {
                    pane.classList.remove('active');
                }
            });
        });
    });

    // Crawl live URL data
    const seoBtnCrawl = document.getElementById('seo-btn-crawl');
    if (seoBtnCrawl) {
        seoBtnCrawl.addEventListener('click', async () => {
            const urlVal = document.getElementById('seo-url').value.trim();
            if (!urlVal) {
                alert('Zadejte prosím URL adresu, kterou chcete nacrawlovat.');
                return;
            }

            const originalBtnHtml = seoBtnCrawl.innerHTML;
            seoBtnCrawl.disabled = true;
            seoBtnCrawl.innerHTML = '<i data-lucide="refresh-cw" class="spin" style="width: 14px; height: 14px;"></i>';
            lucide.createIcons();

            try {
                const response = await fetch('/api/seo/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: urlVal })
                });

                const data = await response.json();
                if (data.success) {
                    document.getElementById('seo-current-title').value = data.title;
                    document.getElementById('seo-current-desc').value = data.description;
                    document.getElementById('seo-current-h1').value = data.h1;

                    // Suggest keyword if currently empty
                    const kwInput = document.getElementById('seo-kw');
                    if (kwInput && !kwInput.value.trim() && data.h1) {
                        kwInput.value = data.h1.toLowerCase();
                    }

                    alert('Data z live URL byla úspěšně stažena a předvyplněna do formuláře!');
                } else {
                    alert(`Chyba při stahování URL: ${data.error}`);
                }
            } catch (err) {
                alert(`Chyba připojení k serveru: ${err.message}`);
            } finally {
                seoBtnCrawl.innerHTML = originalBtnHtml;
                seoBtnCrawl.disabled = false;
                lucide.createIcons();
            }
        });
    }

    // Single Form Submit
    const seoSingleForm = document.getElementById('seo-single-form');
    const seoSingleResult = document.getElementById('seo-single-result');
    const seoSingleEmpty = document.getElementById('seo-single-empty');
    const seoSingleLoader = document.getElementById('seo-single-loader');

    const seoResultGoogleUrl = document.getElementById('seo-result-google-url');
    const seoResultGoogleTitle = document.getElementById('seo-result-google-title');
    const seoResultGoogleDesc = document.getElementById('seo-result-google-desc');

    const seoResultTitle = document.getElementById('seo-result-title');
    const seoResultDesc = document.getElementById('seo-result-desc');
    const seoResultH1 = document.getElementById('seo-result-h1');
    const seoResultBreak = document.getElementById('seo-result-break');
    const seoResultSmycka = document.getElementById('seo-result-smycka');
    const seoResultRizika = document.getElementById('seo-result-rizika');

    const seoCounterTitle = document.getElementById('seo-counter-title');
    const seoCounterDesc = document.getElementById('seo-counter-desc');
    const seoCounterH1 = document.getElementById('seo-counter-h1');

    function updateSeoCounters(title, desc, h1) {
        updateSeoCounter(seoCounterTitle, title.length, 'title');
        updateSeoCounter(seoCounterDesc, desc.length, 'desc');
        updateSeoCounter(seoCounterH1, h1.length, 'h1');
    }

    function updateSeoCounter(element, count, type) {
        element.textContent = `${count} znaků`;
        element.className = 'char-counter';
        if (type === 'title') {
            if (count >= 50 && count <= 58) {
                element.classList.add('optimal');
            } else if (count <= 60) {
                element.classList.add('warning');
            } else {
                element.classList.add('exceeded');
            }
        } else if (type === 'desc') {
            if (count >= 120 && count <= 155) {
                element.classList.add('optimal');
            } else {
                element.classList.add('exceeded');
            }
        } else if (type === 'h1') {
            if (count <= 70) {
                element.classList.add('optimal');
            } else {
                element.classList.add('exceeded');
            }
        }
    }

    seoSingleForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const urlVal = document.getElementById('seo-url').value.trim();
        const kwVal = document.getElementById('seo-kw').value.trim();
        const intentVal = document.getElementById('seo-intent').value;
        const typeVal = document.getElementById('seo-type').value;
        const uspVal = document.getElementById('seo-usp').value.trim();
        const brandVal = document.getElementById('seo-brand').value.trim();
        const serpVal = document.getElementById('seo-serp').value.trim();
        const modelVal = document.getElementById('seo-model').value;
        const simulateVal = document.getElementById('seo-single-simulate').checked;

        const currentTitle = document.getElementById('seo-current-title').value.trim();
        const currentDesc = document.getElementById('seo-current-desc').value.trim();
        const currentH1 = document.getElementById('seo-current-h1').value.trim();

        seoSingleLoader.style.display = 'flex';

        if (simulateVal) {
            // Client-side simulation
            setTimeout(() => {
                const mockResult = {
                    url: urlVal,
                    title: `${kwVal.charAt(0).toUpperCase() + kwVal.slice(1)} do košíčku J - 47 střihů | ${brandVal}`,
                    title_znaku: (`${kwVal.charAt(0).toUpperCase() + kwVal.slice(1)} do košíčku J - 47 střihů | ${brandVal}`).length,
                    description: `Hledáte ${kwVal}? 47 česky šitých střihů prádla Triola do košíčku J – zjistěte v našem e-shopu, který z nich vám padne bez zarývání.`,
                    desc_znaku: `Hledáte ${kwVal}? 47 česky šitých střihů prádla Triola do košíčku J – zjistěte v našem e-shopu, který z nich vám padne bez zarývání.`.length,
                    h1: `${kwVal.charAt(0).toUpperCase() + kwVal.slice(1)}: 47 českých střihů`,
                    pattern_break: "Číslo 47 + konkrétní limit košíčku J porušuje běžný vzor.",
                    smycka: "Otázka 'který vám padne bez zarývání' otevírá informační mezeru.",
                    rizika: "Simulovaná data (lokální test)."
                };
                displaySeoSingleResult(mockResult);
                seoSingleLoader.style.display = 'none';
            }, 600);
            return;
        }

        try {
            const response = await fetch('/api/seo/generate-single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: urlVal,
                    primarni_kw: kwVal,
                    intent: intentVal,
                    typ_stranky: typeVal,
                    usp: uspVal,
                    brand: brandVal,
                    konkurence_serp: serpVal,
                    soucasny_title: currentTitle,
                    soucasna_desc: currentDesc,
                    soucasny_h1: currentH1,
                    model_key: modelVal
                })
            });

            const data = await response.json();
            if (data.success) {
                displaySeoSingleResult(data.result);
            } else {
                alert(`Chyba při generování: ${data.error}`);
            }
        } catch (err) {
            alert(`Chyba připojení k serveru: ${err.message}`);
        } finally {
            seoSingleLoader.style.display = 'none';
        }
    });

    function displaySeoSingleResult(result) {
        seoResultGoogleUrl.textContent = `https://www.triola.cz${result.url.startsWith('/') ? '' : '/'}${result.url}`;
        seoResultGoogleTitle.textContent = result.title;
        seoResultGoogleDesc.textContent = result.description;

        seoResultTitle.value = result.title;
        seoResultDesc.value = result.description;
        seoResultH1.value = result.h1;

        seoResultBreak.textContent = result.pattern_break || 'Není k dispozici.';
        seoResultSmycka.textContent = result.smycka || 'Není k dispozici.';
        seoResultRizika.textContent = result.rizika || 'Žádná detekovaná rizika.';

        updateSeoCounters(result.title, result.description, result.h1);

        seoSingleEmpty.style.display = 'none';
        seoSingleResult.style.display = 'block';
    }

    // Copy SEO Results
    document.querySelectorAll('.btn-copy-seo').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const inputEl = document.getElementById(targetId);
            if (!inputEl) return;

            navigator.clipboard.writeText(inputEl.value).then(() => {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i data-lucide="check" style="color: var(--success); width: 16px;"></i>';
                lucide.createIcons();
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    lucide.createIcons();
                }, 1500);
            });
        });
    });

    // SEO Batch Elements
    const seoBatchUploadArea = document.getElementById('seo-batch-upload-area');
    const seoBatchFileInput = document.getElementById('seo-batch-file-input');
    const seoBatchUploadLink = document.getElementById('seo-batch-upload-link');
    const seoBatchFileSummary = document.getElementById('seo-batch-file-summary');
    const seoBatchFilenameEl = document.getElementById('seo-batch-filename');
    const seoBatchRowsCountEl = document.getElementById('seo-batch-rows-count');
    const seoBatchRemoveFileBtn = document.getElementById('seo-batch-remove-file-btn');
    const seoBatchModelSelect = document.getElementById('seo-batch-model-select');
    const seoBatchSimulateCheckbox = document.getElementById('seo-batch-simulate-checkbox');
    const seoBatchStartBtn = document.getElementById('seo-batch-start-btn');
    const seoBatchDownloadBtn = document.getElementById('seo-batch-download-btn');
    const seoBatchProgressPanel = document.getElementById('seo-batch-progress-panel');
    const seoBatchProgressText = document.getElementById('seo-batch-progress-text');
    const seoBatchProgressBar = document.getElementById('seo-batch-progress-bar');
    const seoBatchTableBody = document.getElementById('seo-batch-table-body');

    const seoBatchPreviewModal = document.getElementById('seo-batch-preview-modal');
    const closeSeoBatchPreviewBtn = document.getElementById('close-seo-batch-preview-btn');

    let seoBatchFilename = '';
    let seoBatchRows = [];
    let seoBatchIsProcessing = false;
    let seoBatchCancelRequested = false;

    if (seoBatchUploadLink) {
        seoBatchUploadLink.addEventListener('click', (e) => {
            e.stopPropagation();
            seoBatchFileInput.click();
        });
    }

    if (seoBatchUploadArea) {
        seoBatchUploadArea.addEventListener('click', (e) => {
            if (e.target !== seoBatchUploadLink) {
                seoBatchFileInput.click();
            }
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            seoBatchUploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                seoBatchUploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            seoBatchUploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                seoBatchUploadArea.classList.remove('dragover');
            }, false);
        });

        seoBatchUploadArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleSeoBatchUpload(files[0]);
            }
        });
    }

    if (seoBatchFileInput) {
        seoBatchFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleSeoBatchUpload(e.target.files[0]);
            }
        });
    }

    if (seoBatchRemoveFileBtn) {
        seoBatchRemoveFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            resetSeoBatchState();
        });
    }

    function resetSeoBatchState() {
        if (seoBatchFileInput) seoBatchFileInput.value = '';
        seoBatchFilename = '';
        seoBatchRows = [];
        seoBatchIsProcessing = false;
        seoBatchCancelRequested = false;

        if (seoBatchFileSummary) seoBatchFileSummary.style.display = 'none';
        if (seoBatchUploadArea) seoBatchUploadArea.style.display = 'block';
        if (seoBatchStartBtn) {
            seoBatchStartBtn.disabled = true;
            seoBatchStartBtn.innerHTML = '<i data-lucide="play"></i> <span>Spustit optimalizaci meta tagů</span>';
            seoBatchStartBtn.className = 'btn primary-btn';
        }
        if (seoBatchDownloadBtn) seoBatchDownloadBtn.disabled = true;
        if (seoBatchProgressPanel) seoBatchProgressPanel.style.display = 'none';
        if (seoBatchTableBody) seoBatchTableBody.innerHTML = '';
        if (seoBatchProgressBar) seoBatchProgressBar.style.width = '0%';
        if (seoBatchProgressText) seoBatchProgressText.textContent = 'Optimalizováno 0 z 0';
        lucide.createIcons();
    }

    async function handleSeoBatchUpload(file) {
        if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls') && !file.name.toLowerCase().endsWith('.csv')) {
            alert('Nahrajte prosím soubor typu CSV nebo Excel (.xlsx, .xls).');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        if (seoBatchUploadArea) seoBatchUploadArea.style.display = 'none';
        if (seoBatchFileSummary) seoBatchFileSummary.style.display = 'flex';
        if (seoBatchFilenameEl) seoBatchFilenameEl.textContent = 'Odesílám a analyzuji soubor...';
        if (seoBatchRowsCountEl) seoBatchRowsCountEl.textContent = '';
        if (seoBatchRemoveFileBtn) seoBatchRemoveFileBtn.disabled = true;

        try {
            const response = await fetch('/api/seo/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.success) {
                seoBatchFilename = data.filename;
                seoBatchRows = data.rows;

                if (seoBatchFilenameEl) seoBatchFilenameEl.textContent = file.name;
                if (seoBatchRowsCountEl) seoBatchRowsCountEl.textContent = `Celkem ${data.total_rows} stránek nalezeno k optimalizaci`;

                if (seoBatchStartBtn) seoBatchStartBtn.disabled = false;
                if (seoBatchRemoveFileBtn) seoBatchRemoveFileBtn.disabled = false;

                renderSeoBatchTableRows(seoBatchRows);
                if (seoBatchProgressPanel) seoBatchProgressPanel.style.display = 'block';
                if (seoBatchProgressText) seoBatchProgressText.textContent = `Připraveno: 0 z ${seoBatchRows.length}`;
                if (seoBatchProgressBar) seoBatchProgressBar.style.width = '0%';
            } else {
                alert(`Chyba při zpracování souboru: ${data.error}`);
                resetSeoBatchState();
            }
        } catch (e) {
            alert(`Chyba připojení k serveru: ${e.message}`);
            resetSeoBatchState();
        }
    }

    function renderSeoBatchTableRows(rows) {
        if (!seoBatchTableBody) return;
        seoBatchTableBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.id = `seo-batch-row-${row.row_num}`;
            tr.style.borderBottom = '1px solid var(--border-color)';
            tr.innerHTML = `
                <td style="padding: 10px; font-weight: 600;">${row.row_num}</td>
                <td style="padding: 10px; word-break: break-all;">${row.url}</td>
                <td style="padding: 10px; font-weight: bold; color: var(--primary);">${row.primarni_kw}</td>
                <td style="padding: 10px;">${row.intent}</td>
                <td style="padding: 10px;">
                    <span class="batch-status-badge pending" id="seo-row-badge-${row.row_num}">Čeká</span>
                </td>
                <td style="padding: 10px; text-align: right;">
                    <button type="button" class="batch-preview-btn" id="seo-preview-btn-${row.row_num}" disabled>
                        <i data-lucide="eye" style="width:14px; height:14px; display:inline-block; vertical-align:middle; margin-right:4px;"></i>
                        <span>Detail</span>
                    </button>
                </td>
            `;
            seoBatchTableBody.appendChild(tr);
        });
        lucide.createIcons();
    }

    if (seoBatchStartBtn) {
        seoBatchStartBtn.addEventListener('click', async () => {
            if (seoBatchIsProcessing) {
                seoBatchCancelRequested = true;
                seoBatchStartBtn.innerHTML = '<i data-lucide="square"></i> <span>Ruším...</span>';
                seoBatchStartBtn.disabled = true;
                lucide.createIcons();
                return;
            }

            seoBatchIsProcessing = true;
            seoBatchCancelRequested = false;
            seoBatchStartBtn.innerHTML = '<i data-lucide="square"></i> <span>Zrušit generování</span>';
            seoBatchStartBtn.className = 'btn danger-btn';
            if (seoBatchRemoveFileBtn) seoBatchRemoveFileBtn.disabled = true;
            if (seoBatchDownloadBtn) seoBatchDownloadBtn.disabled = true;
            lucide.createIcons();

            let processed = 0;
            const total = seoBatchRows.length;
            const model_key = seoBatchSimulateCheckbox.checked ? 'simulation' : seoBatchModelSelect.value;

            for (let i = 0; i < total; i++) {
                if (seoBatchCancelRequested) {
                    break;
                }

                const row = seoBatchRows[i];
                const badge = document.getElementById(`seo-row-badge-${row.row_num}`);
                if (badge) {
                    badge.className = 'batch-status-badge processing';
                    badge.textContent = 'Optimalizuji';
                }

                const tr = document.getElementById(`seo-batch-row-${row.row_num}`);
                if (tr) {
                    tr.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                try {
                    const response = await fetch('/api/seo/process-row', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            filename: seoBatchFilename,
                            row_num: row.row_num,
                            url: row.url,
                            primarni_kw: row.primarni_kw,
                            intent: row.intent,
                            typ_stranky: row.typ_stranky,
                            soucasny_title: row.soucasny_title,
                            soucasna_desc: row.soucasna_desc,
                            soucasny_h1: row.soucasny_h1,
                            usp: row.usp,
                            brand: row.brand,
                            konkurence_serp: row.konkurence_serp,
                            model_key: model_key
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        if (badge) {
                            badge.className = 'batch-status-badge success';
                            badge.textContent = 'Hotovo';
                        }

                        const previewBtn = document.getElementById(`seo-preview-btn-${row.row_num}`);
                        if (previewBtn) {
                            previewBtn.disabled = false;
                            previewBtn.onclick = () => {
                                showSeoBatchPreview(row.url, data.result);
                            };
                        }
                    } else {
                        if (badge) {
                            badge.className = 'batch-status-badge error';
                            badge.textContent = 'Chyba';
                        }
                        console.error(`Chyba optimalizace řádku ${row.row_num}: ${data.error}`);
                    }
                } catch (err) {
                    if (badge) {
                        badge.className = 'batch-status-badge error';
                        badge.textContent = 'Chyba';
                    }
                    console.error(`Chyba připojení na řádku ${row.row_num}:`, err);
                }

                processed++;
                if (seoBatchProgressText) seoBatchProgressText.textContent = `Optimalizováno ${processed} z ${total}`;
                if (seoBatchProgressBar) seoBatchProgressBar.style.width = `${(processed / total) * 100}%`;

                // Wait 1.5 seconds between rows to respect API pacing
                if (i < total - 1 && !seoBatchCancelRequested) {
                    await new Promise(resolve => setTimeout(resolve, 1500));
                }
            }

            seoBatchIsProcessing = false;
            seoBatchStartBtn.innerHTML = '<i data-lucide="play"></i> <span>Spustit optimalizaci meta tagů</span>';
            seoBatchStartBtn.className = 'btn primary-btn';
            seoBatchStartBtn.disabled = false;
            if (seoBatchRemoveFileBtn) seoBatchRemoveFileBtn.disabled = false;
            if (seoBatchDownloadBtn) seoBatchDownloadBtn.disabled = false;
            lucide.createIcons();

            if (seoBatchCancelRequested) {
                alert('Optimalizace byla zrušena uživatelem.');
                seoBatchCancelRequested = false;
            } else {
                alert('Optimalizace všech stránek byla úspěšně dokončena!');
            }
        });
    }

    function showSeoBatchPreview(url, result) {
        document.getElementById('seo-preview-title').textContent = result.title;
        document.getElementById('seo-preview-desc').textContent = result.description;
        document.getElementById('seo-preview-h1').textContent = result.h1;
        document.getElementById('seo-preview-break').textContent = result.pattern_break || 'Není k dispozici.';
        document.getElementById('seo-preview-smycka').textContent = result.smycka || 'Není k dispozici.';
        document.getElementById('seo-preview-rizika').textContent = result.rizika || 'Žádná detekovaná rizika.';

        if (seoBatchPreviewModal) seoBatchPreviewModal.style.display = 'flex';
    }

    if (closeSeoBatchPreviewBtn) {
        closeSeoBatchPreviewBtn.addEventListener('click', () => {
            if (seoBatchPreviewModal) seoBatchPreviewModal.style.display = 'none';
        });
    }

    if (seoBatchPreviewModal) {
        seoBatchPreviewModal.addEventListener('click', (e) => {
            if (e.target === seoBatchPreviewModal) {
                seoBatchPreviewModal.style.display = 'none';
            }
        });
    }

    if (seoBatchDownloadBtn) {
        seoBatchDownloadBtn.addEventListener('click', () => {
            if (!seoBatchFilename) return;
            window.location.href = `/api/seo/download/${seoBatchFilename}`;
        });
    }
});
