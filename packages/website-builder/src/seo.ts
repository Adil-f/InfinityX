export function hasSeoBasics(html: string): boolean {
  return (
    html.includes("<title>") &&
    html.includes('name="description"') &&
    html.includes('rel="canonical"') &&
    html.includes('property="og:title"')
  );
}

export function formSubmitDisabled(html: string): boolean {
  return html.includes('data-submit="disabled"') && html.includes("disabled");
}
