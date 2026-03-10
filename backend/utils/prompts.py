# backend/utils/prompts.py
# Gemini AI prompts for conversion and modification

from typing import Optional

# =====================================================
# CONVERSION PROMPT - Based on blog research
# =====================================================

CONVERSION_SYSTEM_PROMPT = """You are an expert at converting Cypress tests to Playwright tests.

Your task is to convert Cypress test code to Playwright test code while maintaining the exact same test logic and intent.

CRITICAL RULES:
1. If input file is .cy.js → output MUST be .spec.js
2. If input file is .cy.ts → output MUST be .spec.ts
3. Preserve the exact test structure, describe blocks, and test names
4. Handle async/await properly - ALL Playwright operations need await
5. Import necessary Playwright modules at the top
6. Convert ALL Cypress commands to their Playwright equivalents
7. Fix 'this' context issues by using fixtures or module variables
8. Convert synchronous forEach loops to async for...of loops
9. Maintain all test data and assertions

OUTPUT REQUIREMENTS:
- Output ONLY the converted Playwright code
- Do NOT include explanations or comments about the conversion
- Do NOT wrap code in markdown code blocks
- Start directly with imports
"""

CONVERSION_MAPPING = """
COMPLETE CYPRESS TO PLAYWRIGHT CONVERSION MAPPING:

=== NAVIGATION ===
Cypress: cy.visit('https://example.com')
Playwright: await page.goto('https://example.com')

Cypress: cy.go('back')
Playwright: await page.goBack()

Cypress: cy.go('forward')
Playwright: await page.goForward()

Cypress: cy.reload()
Playwright: await page.reload()

=== SELECTORS ===
Cypress: cy.get('#element-id')
Playwright: page.locator('#element-id')

Cypress: cy.get('.class-name')
Playwright: page.locator('.class-name')

Cypress: cy.get('[data-testid="value"]')
Playwright: page.locator('[data-testid="value"]')

Cypress: cy.contains('text')
Playwright: page.getByText('text')

Cypress: cy.get('button').contains('Click me')
Playwright: page.getByRole('button', { name: 'Click me' })

=== INTERACTIONS ===
Cypress: cy.get('#input').type('text')
Playwright: await page.locator('#input').fill('text')

Cypress: cy.get('#input').clear()
Playwright: await page.locator('#input').clear()

Cypress: cy.get('button').click()
Playwright: await page.locator('button').click()

Cypress: cy.get('button').dblclick()
Playwright: await page.locator('button').dblclick()

Cypress: cy.get('button').rightclick()
Playwright: await page.locator('button').click({ button: 'right' })

Cypress: cy.get('select').select('option')
Playwright: await page.locator('select').selectOption('option')

Cypress: cy.get('#checkbox').check()
Playwright: await page.locator('#checkbox').check()

Cypress: cy.get('#checkbox').uncheck()
Playwright: await page.locator('#checkbox').uncheck()

=== ASSERTIONS ===
Cypress: cy.get('#element').should('be.visible')
Playwright: await expect(page.locator('#element')).toBeVisible()

Cypress: cy.get('#element').should('exist')
Playwright: await expect(page.locator('#element')).toHaveCount(1)

Cypress: cy.get('#element').should('not.exist')
Playwright: await expect(page.locator('#element')).toHaveCount(0)

Cypress: cy.get('#element').should('have.text', 'expected')
Playwright: await expect(page.locator('#element')).toHaveText('expected')

Cypress: cy.get('#element').should('contain', 'partial')
Playwright: await expect(page.locator('#element')).toContainText('partial')

Cypress: cy.get('#element').should('have.value', 'value')
Playwright: await expect(page.locator('#element')).toHaveValue('value')

Cypress: cy.get('#element').should('have.attr', 'href', '/path')
Playwright: await expect(page.locator('#element')).toHaveAttribute('href', '/path')

Cypress: cy.get('#element').should('have.class', 'active')
Playwright: await expect(page.locator('#element')).toHaveClass(/active/)

Cypress: cy.url().should('include', '/dashboard')
Playwright: await expect(page).toHaveURL(/.*dashboard/)

Cypress: cy.url().should('eq', 'https://example.com/page')
Playwright: await expect(page).toHaveURL('https://example.com/page')

Cypress: cy.title().should('eq', 'Page Title')
Playwright: await expect(page).toHaveTitle('Page Title')

=== WAITS ===
Cypress: cy.wait(1000)
Playwright: await page.waitForTimeout(1000)

Cypress: cy.get('#element').should('be.visible')
Playwright: await page.locator('#element').waitFor({ state: 'visible' })

Cypress: cy.get('#element', { timeout: 10000 })
Playwright: await page.locator('#element').waitFor({ timeout: 10000 })

=== NETWORK INTERCEPTION ===
Cypress: cy.intercept('GET', '/api/users', { fixture: 'users.json' }).as('getUsers')
Playwright: await page.route('**/api/users', route => route.fulfill({ path: './fixtures/users.json' }))

Cypress: cy.wait('@getUsers')
Playwright: await page.waitForResponse(response => response.url().includes('/api/users') && response.status() === 200)

=== FIXTURES ===
Cypress: cy.fixture('users.json').then(data => { ... })
Playwright: 
import usersData from './fixtures/users.json'
// Use usersData directly

=== COOKIES & LOCAL STORAGE ===
Cypress: cy.setCookie('name', 'value')
Playwright: await context.addCookies([{ name: 'name', value: 'value', url: 'https://example.com' }])

Cypress: cy.getCookie('name')
Playwright: await context.cookies()

Cypress: cy.clearCookies()
Playwright: await context.clearCookies()

Cypress: cy.window().then(win => win.localStorage.setItem('key', 'value'))
Playwright: await page.evaluate(() => localStorage.setItem('key', 'value'))

=== VIEWPORT ===
Cypress: cy.viewport(1280, 720)
Playwright: await page.setViewportSize({ width: 1280, height: 720 })

=== SCREENSHOTS ===
Cypress: cy.screenshot()
Playwright: await page.screenshot({ path: 'screenshot.png' })

=== FILE UPLOAD ===
Cypress: cy.get('input[type="file"]').selectFile('path/to/file')
Playwright: await page.locator('input[type="file"]').setInputFiles('path/to/file')
"""

CONVERSION_USER_PROMPT_TEMPLATE = """
Convert the following Cypress test to Playwright.

Filename: {filename}
File Type: {file_type}

Cypress Code:
```
{cypress_code}
```

Apply all conversion rules and examples provided. Output ONLY the converted Playwright code without any explanations or markdown formatting.
"""

# =====================================================
# MODIFICATION PROMPT - For fixing converted code
# =====================================================

MODIFICATION_SYSTEM_PROMPT = """You are an expert at fixing and improving Playwright test code.

A user has converted a Cypress test to Playwright but encountered issues. Your task is to analyze the problem and provide a corrected version of the Playwright code.

CRITICAL RULES:
1. Maintain the same test logic and intent
2. Fix ONLY the reported issues
3. Keep the same file extension (.spec.js or .spec.ts)
4. Output ONLY the corrected code
5. Do NOT include explanations or comments
6. Ensure all Playwright operations have await
7. Use proper waits and assertions
8. Handle async operations correctly

COMMON ISSUES AND FIXES:

1. TIMEOUT ERRORS:
   - Add explicit waits: await page.waitForSelector()
   - Use waitForLoadState: await page.waitForLoadState('networkidle')
   - Increase timeout: await locator.click({ timeout: 30000 })

2. LOCATOR NOT FOUND:
   - Use better selectors: getByRole, getByText, getByLabel
   - Add waits before interaction
   - Check element visibility: await expect(locator).toBeVisible()

3. ASSERTION FAILURES:
   - Use correct Playwright assertions
   - Add waits before assertions
   - Check exact vs partial matches

4. ASYNC/AWAIT ISSUES:
   - Ensure ALL Playwright calls have await
   - Use proper async function syntax
   - Handle Promises correctly

5. FLAKY TESTS:
   - Add auto-waiting mechanisms
   - Use page.waitForResponse for API calls
   - Avoid hard-coded waits, use smart waits

OUTPUT REQUIREMENTS:
- Output ONLY the corrected Playwright code
- Do NOT wrap in markdown code blocks
- Start directly with imports
"""

MODIFICATION_USER_PROMPT_TEMPLATE = """
The converted Playwright test has the following issue:

User Description: {user_query}

{error_section}

ORIGINAL CYPRESS CODE (for reference):
```
{cypress_code}
```

CURRENT PLAYWRIGHT CODE (with issues):
```
{playwright_code}
```

Analyze the issue and provide the corrected Playwright code. Output ONLY the fixed code without explanations.
"""

def build_conversion_prompt(filename: str, file_type: str, cypress_code: str) -> str:
    """Build complete conversion prompt for Gemini"""
    system_content = f"{CONVERSION_SYSTEM_PROMPT}\n\n{CONVERSION_MAPPING}"
    
    user_content = CONVERSION_USER_PROMPT_TEMPLATE.format(
        filename=filename,
        file_type=file_type,
        cypress_code=cypress_code
    )
    
    return system_content, user_content

def build_modification_prompt(
    user_query: str,
    error_message: Optional[str],
    cypress_code: str,
    playwright_code: str
) -> tuple:
    """Build complete modification prompt for Gemini"""
    
    error_section = ""
    if error_message:
        error_section = f"\nError Message:\n```\n{error_message}\n```"
    
    user_content = MODIFICATION_USER_PROMPT_TEMPLATE.format(
        user_query=user_query,
        error_section=error_section,
        cypress_code=cypress_code,
        playwright_code=playwright_code
    )
    
    return MODIFICATION_SYSTEM_PROMPT, user_content