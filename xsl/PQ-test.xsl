<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:marc="http://www.loc.gov/MARC21/slim"
	exclude-result-prefixes="xs">
<!--created by Perry Willett -->
<!--v1.0 2017-08-25 -->
<!--tests if record exists -->
<!--v1.2 2018-09-27 -->
<!--tests if PQ MARC record has 856 field -->
<!--v1.21 2018-10-22 -->
<!--fixed bug -->
<xsl:output method="text" encoding="UTF-8"/>
<xsl:key name="ISBN" match="row" use="value"/>
<xsl:variable name="lookupISBN" select="document('PQ-Merritt-match.xml')"/>

<xsl:template match="/marc:collection">
<xsl:for-each select ="//marc:record">
    <xsl:call-template name="lookupPQLink"><xsl:with-param name="isbn" select="./marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/></xsl:call-template>
</xsl:for-each>
</xsl:template>

<xsl:template name="lookupPQLink">
        <xsl:param name="isbn" />
        <xsl:choose>
                <xsl:when test="string-length($lookupISBN/key('ISBN',$isbn)/value[@column = '2'])=0">
                    <xsl:text>ERROR&#x9;</xsl:text>
                    <xsl:value-of select="$isbn"/>           
                    <xsl:text>&#xA;</xsl:text>
                </xsl:when>
		<xsl:when test="string-length(./marc:datafield[@tag = '856']/marc:subfield[@code = 'u'])=0">
                    <xsl:text>ERROR: missing 856&#x9;</xsl:text>
                    <xsl:value-of select="$isbn"/>
                    <xsl:text>&#xA;</xsl:text>
                </xsl:when>
        </xsl:choose>
</xsl:template>
</xsl:stylesheet>
