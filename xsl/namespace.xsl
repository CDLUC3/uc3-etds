<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:marc="http://www.loc.gov/MARC21/slim" version="1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
	<xsl:output method="xml" indent="no" encoding="utf-8" omit-xml-declaration="no" />
	<xsl:template match="*">
		<xsl:element name="marc:{local-name(.)}">
			<xsl:apply-templates select="@*|*|text()"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="@*">
		<xsl:attribute name="{name(.)}"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
</xsl:stylesheet>

