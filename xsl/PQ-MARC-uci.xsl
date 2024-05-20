<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:marc="http://www.loc.gov/MARC21/slim"
	exclude-result-prefixes="xs">
<!--created by Perry Willett -->
<!--v1.1 2014-04-07 -->
<!--designed to transform Proquest MARC records for ETDs to meet UC Merced library requirements for MARC records -->
<!--v1.1: added error testing for lookup -->
<xsl:output method="xml" encoding="UTF-8"/>
<xsl:key name="ISBN" match="row" use="value"/>
<xsl:key name="subject" match="row" use="value"/>
<xsl:variable name="lookupISBN" select="document('PQ-Merritt-match.xml')"/>
<!--uci-subjects xml used for addition of new UCI degrees to database -->
<xsl:variable name="lookupSubj" select="document('uci-subjects.xml')"/>
<xsl:template match="@*|node()">
	<xsl:copy>
		<xsl:apply-templates select="@*|node()"/>
	</xsl:copy>
</xsl:template>

<xsl:template match="marc:leader">
<!--should be constant -->
	<marc:leader><xsl:text xml:space="preserve">00000nam a22     Ki 4500</xsl:text></marc:leader>
</xsl:template>
<xsl:template match="marc:controlfield[@tag='001']"/>
<xsl:template match="marc:controlfield[@tag='005']">
	<marc:controlfield tag="006">
		<xsl:text xml:space="preserve">m|||||o||d||||||||</xsl:text>
	</marc:controlfield>
	<marc:controlfield tag="007">
		<xsl:text>cr||||||||||||</xsl:text>
	</marc:controlfield>
</xsl:template>
<xsl:template match="marc:controlfield[@tag = '008']">
<xsl:variable name="degree" select="//marc:datafield[@tag = '791']/marc:subfield[@code = 'a']"/>
	<marc:controlfield tag="008">
		<xsl:value-of select="substring(.,1,6)"/>
		<xsl:text>s</xsl:text>
		<xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/>
		<xsl:text xml:space="preserve">    cau     om    000 0 </xsl:text>
		<xsl:call-template name="calculate_lang_code">
			<xsl:with-param name="PQ_lang_code" select="../marc:datafield[@tag = '793']/marc:subfield[@code = 'a']"/>
		</xsl:call-template>
		<xsl:text xml:space="preserve"> d</xsl:text>
	</marc:controlfield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='035']">
	<xsl:variable name="isbn">
		<xsl:value-of select="../marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/>
	</xsl:variable>
	<xsl:variable name="mrt-localID" select="$lookupISBN/key('ISBN',$isbn)/value[@column = '3']"/>
	<marc:datafield tag="035" ind1=" " ind2=" ">
		<marc:subfield code="a">uci:<xsl:value-of select="substring-after($mrt-localID, 'PQETD:uci')"/></marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='040']">
	<marc:datafield tag="040" ind1=" " ind2=" ">
		<marc:subfield code="a"><xsl:value-of select="./marc:subfield[@code='a']"/></marc:subfield>
		<marc:subfield code="b">eng</marc:subfield>
		<marc:subfield code="e">rda</marc:subfield>
		<marc:subfield code="c"><xsl:value-of select="./marc:subfield[@code='c']"/></marc:subfield>
	</marc:datafield>
	<marc:datafield tag="099" ind1=" " ind2=" ">
	<xsl:variable name="degree" select="..//marc:datafield[@tag = '791']/marc:subfield[@code = 'a']"/>
		<marc:subfield code="a">
			<xsl:text>LD</xsl:text>
		</marc:subfield>
		<marc:subfield code="a">
			<xsl:choose>
				<xsl:when test="contains($degree, 'Ph.')">
					<xsl:text>791.9</xsl:text>
				</xsl:when>
				<xsl:when test="contains($degree, 'Ed.')">
					<xsl:text>791.9</xsl:text>
				</xsl:when>
				<xsl:when test="contains($degree, 'M.')">
					<xsl:text>791.8</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>ERROR</xsl:text>
					<!-- Added value-of statement to debug problematic value population -->
					<xsl:value-of select="$degree"/>
				</xsl:otherwise>
			</xsl:choose>
		</marc:subfield>
		<marc:subfield code="a">
			<xsl:call-template name="lookupUCISubj"> 
				<xsl:with-param name="subj_area"> 
					<xsl:choose>
						<!-- 2023-08-17 Added new when blocks for open paren, and FNP string -->
						<xsl:when test="contains(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ' -')">
							<xsl:value-of select="substring-before(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ' -')"/>
						</xsl:when>
						<xsl:when test="contains(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ' (')">
							<xsl:value-of select="substring-before(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ' (')"/>
						</xsl:when>
						<xsl:when test="contains(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ', FNP (')">
							<xsl:value-of select="substring-before(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], ', FNP (')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="substring-before(../marc:datafield[@tag = '710']/marc:subfield[@code = 'b'], '.')"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:with-param>
			</xsl:call-template>
		</marc:subfield>
		<marc:subfield code="a">
			<xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/>
		</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='100']">
	<xsl:variable name="full100" select="./marc:subfield[@code='a']"/>
	<marc:datafield tag="100" ind1="3" ind2=" ">
	<!-- LastName+, GivenName. -->
	<xsl:analyze-string select="$full100" regex="^([^,]*),\s([^\s,]+)\.$">
		<xsl:matching-substring> 
			<marc:subfield code="a"><xsl:value-of select="regex-group(1)"/><xsl:text>, </xsl:text><xsl:value-of select="regex-group(2)"/>
			<xsl:if test="string-length(regex-group(2))=1">
				<xsl:text>.</xsl:text>
			</xsl:if>
			<xsl:text>, </xsl:text>
			</marc:subfield>
		</xsl:matching-substring>
	</xsl:analyze-string>
	<!-- LastName+, GivenName+ MiddleName -->
	<xsl:analyze-string select="$full100" regex="^([^,]*),\s([^,]+)\s([^,]+)\.$">
		<xsl:matching-substring> 
			<marc:subfield code="a"><xsl:value-of select="regex-group(1)"/><xsl:text>, </xsl:text><xsl:value-of select="regex-group(2)"/><xsl:text> </xsl:text><xsl:value-of select="regex-group(3)"/>
			<xsl:if test="string-length(regex-group(3))=1">
				<xsl:text>.</xsl:text>
			</xsl:if>
			<xsl:text>, </xsl:text>
			</marc:subfield>
		</xsl:matching-substring>
	</xsl:analyze-string>
	<!-- Lastname+, GivenName+, Suffix. -->
	<xsl:analyze-string select="$full100" regex="^([^,]+),\s(.*),\s(.*)\.$">
		<xsl:matching-substring> 
			<marc:subfield code="a"><xsl:value-of select="regex-group(1)"/><xsl:text> </xsl:text><xsl:value-of select="regex-group(2)"/>
			<xsl:if test="string-length(regex-group(2))=1">
				<xsl:text>.</xsl:text>
			</xsl:if><xsl:text>, </xsl:text><xsl:value-of select="regex-group(3)"/><xsl:if test="regex-group(3)='Jr' or regex-group(3)='Sr'">.</xsl:if>
			<xsl:text>, </xsl:text>
			</marc:subfield>
		</xsl:matching-substring>
	</xsl:analyze-string>
	<marc:subfield code="e">author.</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='245']">
	<marc:datafield tag="245">
		<xsl:attribute name="ind1"><xsl:value-of select="./@ind1"/></xsl:attribute>
		<xsl:attribute name="ind2"><xsl:value-of select="./@ind2"/></xsl:attribute>
		<xsl:variable name="full245" select="normalize-space(./marc:subfield[@code='a'])"/>
		<xsl:variable name="etdTitle">
			<xsl:choose>
				<xsl:when test="substring($full245, (string-length($full245)), 1)='.'">
					<xsl:value-of select="substring($full245, 1, (string-length($full245)-1))"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$full245"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="full100" select="../marc:datafield[@tag='100']/marc:subfield[@code='a']"/>
		<xsl:variable name="etdAuthor">
			<!-- LastName+, GivenName. -->
			<xsl:analyze-string select="$full100" regex="^([^,]*),\s([^\s,]*)\.$">
				<xsl:matching-substring> 
					<xsl:value-of select="regex-group(2)"/><xsl:if test="string-length(regex-group(2))=1"><xsl:text>.</xsl:text></xsl:if><xsl:text> </xsl:text><xsl:value-of select="regex-group(1)"/><xsl:text>.</xsl:text>
				</xsl:matching-substring>
			</xsl:analyze-string>
			<!-- LastName+, GivenName+ MiddleName. -->
			<xsl:analyze-string select="$full100" regex="^([^,]*),\s([^,]+)\s([^,]+)\.$">
				<xsl:matching-substring> 
					<xsl:value-of select="regex-group(2)"/><xsl:text> </xsl:text><xsl:value-of select="regex-group(3)"/><xsl:if test="string-length(regex-group(3))=1"><xsl:text>.</xsl:text></xsl:if><xsl:text> </xsl:text><xsl:value-of select="regex-group(1)"/><xsl:text>.</xsl:text>
				</xsl:matching-substring>
			</xsl:analyze-string>
			<!-- LastName, Name+, Suffix. -->
			<xsl:analyze-string select="$full100" regex="^([^,]*),\s(.*),\s(.*)\.$">
				<xsl:matching-substring>
					<xsl:value-of select="regex-group(2)"/><xsl:text> </xsl:text><xsl:value-of select="regex-group(1)"/><xsl:text>, </xsl:text><xsl:value-of select="regex-group(3)"/><xsl:text>.</xsl:text>
				</xsl:matching-substring>
			</xsl:analyze-string>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="contains($etdTitle, ': ')">
				<marc:subfield code="a">
					<xsl:value-of select="substring-before($etdTitle, ': ')"/>
					<xsl:text> :</xsl:text>
				</marc:subfield>
				<marc:subfield code="b">
					<xsl:value-of select="substring-after($etdTitle, ': ')"/><xsl:text> / </xsl:text>
				</marc:subfield>
			</xsl:when>
			<xsl:otherwise>
				<marc:subfield code="a">
					<xsl:value-of select="$etdTitle"/><xsl:text> / </xsl:text>
				</marc:subfield>
			</xsl:otherwise>
		</xsl:choose>
		<marc:subfield code="c">by <xsl:value-of select="$etdAuthor"/>
		</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='260']"/>
<xsl:template match="marc:datafield[@tag='300']">
	<marc:datafield tag="264" ind1=" " ind2="1">
		<marc:subfield code="a">Irvine, Calif. :</marc:subfield>
		<marc:subfield code="b">University of California, Irvine, </marc:subfield>
		<marc:subfield code="c">[<xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/>]</marc:subfield> 
	</marc:datafield>
	<marc:datafield tag="300" ind1=" " ind2=" "><marc:subfield code="a">1 online resource (<xsl:value-of select="substring-before(./marc:subfield[@code = 'a'], ' p.')"/> pages)</marc:subfield> 
	</marc:datafield>
	<marc:datafield tag="336" ind1=" " ind2=" ">
		<marc:subfield code="a">text</marc:subfield>
		<marc:subfield code="2">rdacontent</marc:subfield>
	</marc:datafield>
	<marc:datafield tag="337" ind1=" " ind2=" ">
		<marc:subfield code="a">computer</marc:subfield>
		<marc:subfield code="2">rdamedia</marc:subfield>
	</marc:datafield>
	<marc:datafield tag="338" ind1=" " ind2=" ">
		<marc:subfield code="a">online resource</marc:subfield>
		<marc:subfield code="2">rdacarrier</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag='500']"/>
<xsl:template match="marc:datafield[@tag='502']">
	<marc:datafield tag="502" ind1=" " ind2=" ">
		<marc:subfield code="b"><xsl:value-of select="../marc:datafield[@tag = '791']/marc:subfield[@code = 'a']"/></marc:subfield>
		<marc:subfield code="c">University of California, Irvine</marc:subfield>
		<marc:subfield code="d"><xsl:value-of select="../marc:datafield[@tag = '792']/marc:subfield[@code = 'a']"/><xsl:text>.</xsl:text></marc:subfield>
	</marc:datafield>
	<marc:datafield tag="504" ind1=" " ind2=" ">
		<marc:subfield code="a">Includes bibliographical references.</marc:subfield>
	</marc:datafield>
	<xsl:variable name="abstract">
		<xsl:for-each select="../marc:datafield[@tag = '520']/marc:subfield[@code = 'a']">
				<xsl:value-of select="." />
		</xsl:for-each>
	</xsl:variable>
	<xsl:if test="string-length($abstract)&gt;0">
		<marc:datafield tag="520" ind1="3" ind2=" ">
			<xsl:if test="string-length($abstract)&lt;9980">
				<marc:subfield code="a">
					<xsl:value-of select="$abstract" />
				</marc:subfield>  
			</xsl:if>
		    <xsl:if test="string-length($abstract)&gt;9980">
				<marc:subfield code="a">
					<xsl:value-of select="substring($abstract, 1, 9980)" />...</marc:subfield>
			</xsl:if>
		</marc:datafield>
	</xsl:if>
</xsl:template>
<xsl:template match="marc:datafield[@tag='506']"/>
<xsl:template match="marc:datafield[@tag='520']"/>
<xsl:template match="marc:datafield[@tag='590']">
	<marc:datafield tag="588" ind1=" " ind2=" ">
		<marc:subfield code="a">
			<xsl:text xml:space="preserve">Description based on online resource; title from PDF title page (ProQuest, viewed )</xsl:text>
		</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag = '650']">
	<marc:datafield tag="653" ind1=" " ind2=" "><xsl:copy-of select="*"/></marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag = '690']"/>
<xsl:template match="marc:datafield[@tag = '710']">
	<marc:datafield tag="655" ind1=" " ind2="7">
		<marc:subfield code="a">Dissertations, Academic</marc:subfield>
		<marc:subfield code="z">University of California, Irvine</marc:subfield>
		<xsl:choose>
			<xsl:when test="contains(./marc:subfield[@code = 'b'], ' -')">
				<marc:subfield code="x"><xsl:value-of select="substring-before(./marc:subfield[@code = 'b'], ' -')"/><xsl:text>.</xsl:text></marc:subfield>
			</xsl:when>
			<xsl:otherwise>
				<marc:subfield code="x"><xsl:value-of select="substring-before(./marc:subfield[@code = 'b'], '.')"/><xsl:text>.</xsl:text></marc:subfield>
			</xsl:otherwise>
		</xsl:choose>
		<marc:subfield code="2">local</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag = '773']"/>
<xsl:template match="marc:datafield[@tag = '790']"/>
<xsl:template match="marc:datafield[@tag = '791']"/>
<xsl:template match="marc:datafield[@tag = '792']"/>
<xsl:template match="marc:datafield[@tag = '793']">
	<marc:datafield tag="793" ind1="0" ind2="8">
		<marc:subfield code="a">UCI electronic theses and dissertations</marc:subfield>
	</marc:datafield>
</xsl:template>
<xsl:template match="marc:datafield[@tag = '856']">
	<xsl:variable name="isbn">
		<xsl:value-of select="../marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/>
	</xsl:variable>
	<xsl:variable name="embargo_code">
		<xsl:value-of select="$lookupISBN/key('ISBN',$isbn)/value[@column = '5']"/>
	</xsl:variable>
	<xsl:variable name="embargo_end_date">
		<xsl:value-of select="$lookupISBN/key('ISBN',$isbn)/value[@column = '6']"/>
	</xsl:variable>
	<xsl:choose>
		<xsl:when test="$embargo_code=0">
			<marc:datafield tag="856" ind1="4" ind2="0"><marc:subfield code="z">Open Access via eScholarship</marc:subfield><marc:subfield code="u"><xsl:call-template name="lookupEScholLink"><xsl:with-param name="isbn" select="$isbn"/></xsl:call-template></marc:subfield></marc:datafield>
			<marc:datafield tag="856" ind1="4" ind2="0"><marc:subfield code="z">Proquest. Restricted to UCI.</marc:subfield>
			<marc:subfield code="u">http://search.proquest.com/docview/<xsl:call-template name="lookupPQLink"><xsl:with-param name="isbn" select="$isbn"/></xsl:call-template></marc:subfield></marc:datafield>	
		</xsl:when>
		<xsl:otherwise>
			<marc:datafield tag="856" ind1="4" ind2="0">
				<marc:subfield code="z">eScholarship. Due to student requested embargo, full text not available until <xsl:call-template name="format_embargo_enddate">
					<xsl:with-param name="embargo_enddate_string" select="$embargo_end_date"/>
				</xsl:call-template>
				</marc:subfield>
				<marc:subfield code="u"><xsl:call-template name="lookupEScholLink"><xsl:with-param name="isbn" select="$isbn"/></xsl:call-template></marc:subfield>
			</marc:datafield>
			<marc:datafield tag="856" ind1="4" ind2="0">
				<marc:subfield code="z">Proquest. Restricted to UCI. Due to student requested embargo, full text not available until <xsl:call-template name="format_embargo_enddate">
					<xsl:with-param name="embargo_enddate_string" select="$embargo_end_date"/>
				</xsl:call-template></marc:subfield>
				<marc:subfield code="u">http://search.proquest.com/docview/<xsl:call-template name="lookupPQLink"><xsl:with-param name="isbn" select="$isbn"/></xsl:call-template></marc:subfield>
			</marc:datafield>
		</xsl:otherwise>
	</xsl:choose> 
<!--	<marc:datafield tag="856" ind1=" " ind2=" "><marc:subfield code="a">UC Access only</marc:subfield>
	<marc:subfield code="u">http://search.proquest.com/docview/<xsl:call-template name="lookupPQLink"><xsl:with-param name="isbn" select="../marc:datafield[@tag = '020']/marc:subfield[@code = 'a']"/></xsl:call-template></marc:subfield></marc:datafield>
-->
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
<xsl:template name="calculate_lang_code">
	<xsl:param name="PQ_lang_code"/>
	<xsl:if test="$PQ_lang_code='English'">eng</xsl:if>
	<xsl:if test="$PQ_lang_code='Spanish'">spa</xsl:if>
</xsl:template>
<xsl:template name="lookupUCISubj">
	<xsl:param name="subj_area" />
	<xsl:choose>
		<xsl:when test="string-length($lookupSubj/key('subject',$subj_area)/value[@column = '1'])!=0">
			<xsl:value-of select="$lookupSubj/key('subject',$subj_area)/value[@column = '1']"/>
		</xsl:when>
		<xsl:otherwise>ERROR: <xsl:value-of select="$subj_area"/></xsl:otherwise>
	</xsl:choose>
</xsl:template>	
<xsl:template name="format_embargo_enddate">
	<xsl:param name="embargo_enddate_string"/>
	<xsl:variable name="formatted_date" as="xs:date">
		<xsl:value-of select="xs:date($embargo_enddate_string)"/>
	</xsl:variable>
	<xsl:value-of select="format-date($formatted_date, '[M01]/[D01]/[Y0001]')"/>
</xsl:template>
</xsl:stylesheet>

