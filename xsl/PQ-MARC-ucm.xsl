<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:marc="http://www.loc.gov/MARC21/slim">
<!--created by Perry Willett -->
<!--v1.1 2014-04-07 -->
<!--designed to transform Proquest MARC records for ETDs to meet UC Merced library requirements for MARC records -->
<!--v1.1: added error testing for lookup -->
<xsl:output method="xml" encoding="UTF-8"/>
<xsl:key name="ISBN" match="row" use="value"/>
<xsl:variable name="lookupISBN" select="document('PQ-Merritt-match.xml')"/>
<xsl:variable name="error" select="ERROR"/>
<xsl:template match="@*|node()">
	<xsl:copy>
		<xsl:apply-templates select="@*|node()"/>
	</xsl:copy>
</xsl:template>

<xsl:template match="marc:leader">
	<marc:leader><xsl:value-of select="concat(substring(../marc:leader,1,6), 't', substring(../marc:leader,8,10),'Ko',substring(../marc:leader,20,6))"/></marc:leader>
</xsl:template>

<xsl:template match="marc:controlfield[@tag = '008']">
	<marc:controlfield tag="008"><xsl:value-of select="concat(substring(../marc:controlfield[@tag = '008'],1,15),'cau',substring(../marc:controlfield[@tag = '008'],19))"/></marc:controlfield>
</xsl:template>

<xsl:template match="marc:datafield[@tag = '260']">
	<marc:datafield tag="260" ind1=" " ind2=" "><marc:subfield code="a">[Merced, CA]</marc:subfield><marc:subfield code="b">University of California, Merced</marc:subfield><marc:subfield code="c"><xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/></marc:subfield></marc:datafield>
</xsl:template>

<xsl:template match="marc:datafield[@tag = '300']">
	<marc:datafield tag="300" ind1=" " ind2=" "><marc:subfield code="a">1 online resource (<xsl:value-of select="substring-before(../marc:datafield[@tag = '300']/marc:subfield[@code = 'a'], ' p.')"/> leaves)</marc:subfield></marc:datafield>
</xsl:template>

<xsl:template match="marc:datafield[@tag = '502']">
	<marc:datafield tag="502" ind1=" " ind2=" "><marc:subfield code="a">Thesis (<xsl:value-of select="../marc:datafield[@tag = '791']"/>)--University of California, Merced, <xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/></marc:subfield></marc:datafield>
</xsl:template>

<xsl:template match="marc:datafield[@tag = '650'][last()]">
	<marc:datafield tag="650" ind1=" " ind2="4"><xsl:copy-of select="*"/></marc:datafield>
	<marc:datafield tag="655" ind1=" " ind2="7"><marc:subfield code="a">Dissertations, Academic</marc:subfield><marc:subfield code="z">University of California, Merced</marc:subfield><marc:subfield code="x"><xsl:value-of select="../marc:datafield[@tag = '650'][1]"/></marc:subfield><marc:subfield code="2">local</marc:subfield></marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag = '690']"/>
<xsl:template match="marc:datafield[@tag = '710']"/>
<xsl:template match="marc:datafield[@tag = '773']"/>
<xsl:template match="marc:datafield[@tag = '790']"/>
<xsl:template match="marc:datafield[@tag = '791']"/>
<xsl:template match="marc:datafield[@tag = '792']"/>
<xsl:template match="marc:datafield[@tag = '793']"/>
<xsl:template match="marc:datafield[@tag = '856']">
	<marc:datafield tag="856" ind1=" " ind2=" "><marc:subfield code="a">Open Access</marc:subfield><marc:subfield code="u">
		<xsl:call-template name="lookupEScholLink">
			<xsl:with-param name="isbn" select="../marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/>
		</xsl:call-template>
	</marc:subfield></marc:datafield>
	<marc:datafield tag="856" ind1=" " ind2=" "><marc:subfield code="a">UC Access only</marc:subfield>
	<marc:subfield code="u">http://search.proquest.com/docview/<xsl:call-template name="lookupPQLink"><xsl:with-param name="isbn" select="../marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/></xsl:call-template></marc:subfield></marc:datafield>
</xsl:template>

<xsl:template name="lookupEScholLink">
	<xsl:param name="isbn" />
	<xsl:choose>
		<xsl:when test="string-length($lookupISBN/key('ISBN',$isbn)/value[@column = '4'])!=0">
			<xsl:value-of select="$lookupISBN/key('ISBN',$isbn)/value[@column = '4']"/>
		</xsl:when>
		<xsl:otherwise>ERROR</xsl:otherwise>
	</xsl:choose>
</xsl:template>	

<xsl:template name="lookupPQLink">
	<xsl:param name="isbn" /> 
	<xsl:choose>
		<xsl:when test="string-length($lookupISBN/key('ISBN',$isbn)/value[@column = '2'])!=0">
			<xsl:value-of select="$lookupISBN/key('ISBN',$isbn)/value[@column = '2']"/>
		</xsl:when>
		<xsl:otherwise>ERROR</xsl:otherwise>
	</xsl:choose>
</xsl:template>	
</xsl:stylesheet>
