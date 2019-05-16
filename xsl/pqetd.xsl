<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:zs="http://www.loc.gov/zing/srw/" xmlns:marc="http://www.loc.gov/MARC21/slim" version="2.0">
<!--created by Perry Willett -->
<!--v1.0 2014-03-24-->
<!--takes ProQuest MARC records retrieved from the PQ XML Gateway, and returns PQ identifier, ISBN, author and title for import into SQL table -->
<xsl:output method="text" encoding="utf-8"/>

	<xsl:template match="/">
	<xsl:choose>
	<xsl:when test="/zs:searchRetrieveResponse/zs:numberOfRecords='1'">
		<xsl:value-of select="/zs:searchRetrieveResponse/zs:records/zs:record/zs:recordData/marc:record/marc:controlfield[@tag='001']"/>
		<xsl:text>&#x9;</xsl:text>
        <xsl:value-of select="/zs:searchRetrieveResponse/zs:records/zs:record/zs:recordData/marc:record/marc:datafield[@tag='020']/marc:subfield[@code='a']"/>
        <xsl:text>&#x9;</xsl:text>
		<xsl:value-of select="/zs:searchRetrieveResponse/zs:records/zs:record/zs:recordData/marc:record/marc:datafield[@tag='100']/marc:subfield[@code='a']"/>
		<xsl:text>&#x9;</xsl:text>
		<xsl:value-of select="normalize-space(/zs:searchRetrieveResponse/zs:records/zs:record/zs:recordData/marc:record/marc:datafield[@tag='245']/marc:subfield[@code='a'])"/>
		<xsl:text>&#xA;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
		<xsl:text>Not found&#x9; &#x9;</xsl:text>
		<xsl:value-of select="//diagnosticMessage[1]"/>
		<xsl:text>&#xA;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	</xsl:template>
</xsl:stylesheet>
