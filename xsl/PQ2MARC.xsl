<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="2.0"  xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema">
<!--First created by Terry Reese and distributed as part of MarcEdit -->
<!--created to transform Proquest metadata to MARC record -->
<!--Modified by Perry Willett -->
<xsl:output method="xml" indent="yes" encoding="iso-8859-1" omit-xml-declaration="yes" /> 
<xsl:key name="local_id" match="row" use="value"/>
<xsl:key name="subject" match="row" use="value"/> 
<xsl:variable name="campus_code" select="/DISS_submission/DISS_description/DISS_institution/DISS_inst_code"/>
<xsl:variable name="fullLocalID" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
<xsl:variable name="localID" select="substring-after($fullLocalID,':')"/>
<xsl:variable name="lookupID" select="document('mrt-eschol-pq.xml')"/>	
<xsl:variable name="lookupSubj" select="document('uci-subjects.xml')"/>	
<xsl:variable name="apos">'</xsl:variable>
<xsl:variable name="quot">"</xsl:variable>
<xsl:variable name="embargo_end_date_string" select="/DISS_submission/DISS_restriction/DISS_sales_restriction/@remove"/>
<xsl:variable name="degree" select="/DISS_submission/DISS_description/DISS_degree"/>
<xsl:variable name="subjectArea" select="substring-before(/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact, ' -')"/>
<xsl:variable name="etdTitle" select="/DISS_submission/DISS_description/DISS_title"/>
<xsl:param name="embargo_code4"/>

<!-- UMI School Codes (DISS_inst_code) for UC campuses:
	ucb:	0028
	ucd:	0029 (note: UCD does not deposit ETDs in Merritt)
	uci:	0030
	ucla:	0031
	ucr:	0032
	ucsd:	0033 
	ucsf:	0034
	ucsb:	0035
	ucsc:	0036
	ucm:	1660
-->
<xsl:template match="/DISS_submission">
	<xsl:choose>
		<xsl:when test="$campus_code='0030'">
			<xsl:call-template name="uci_template"/>
		</xsl:when>
		<xsl:when test="$campus_code='0031'">
			<xsl:call-template name="ucla_template"/>
		</xsl:when>
		<xsl:when test="$campus_code='0033'">
			<xsl:call-template name="ucsd_template"/>
		</xsl:when>
		<xsl:otherwise>
			<xsl:call-template name="exception_template"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>
<xsl:template name="uci_template">
	<marc:record>
		<xsl:variable name="date1" select="normalize-space(DISS_description/DISS_dates/DISS_comp_date)" />
		<xsl:variable name="accept_date" select="normalize-space(DISS_description/DISS_dates/DISS_accept_date)"/>
		<!--Start by building the LDR, 007 and 008 -->
		<!--VESTIGIAL NOTE IN ORIGINAL STYLESHEET: Processing problem is somewhere within the leader or controlfield element-->
		<leader><xsl:text xml:space="preserve">00000nam a22     Ki 4500</xsl:text></leader>  <!-- The first six digits of the 008 field is the current date in YYMMDD format. -->
		<marc:controlfield tag="008">
			<xsl:value-of select="format-date(current-date(),'[Y01][M01][D01]')"/>
			<xsl:text xml:space="preserve">s</xsl:text>
			<xsl:value-of select="/DISS_submission/DISS_description/DISS_dates/DISS_comp_date"/>
			<xsl:text xml:space="preserve">    cau     om    000 0 </xsl:text>
			<xsl:call-template name="calculate_lang_code">
				<xsl:with-param name="PQ_lang_code" select="/DISS_submission/DISS_description/DISS_categorization/DISS_language"/>
			</xsl:call-template>
			<xsl:text xml:space="preserve"> d</xsl:text>
		</marc:controlfield>
		<marc:controlfield tag="006">
			<xsl:text xml:space="preserve">m     o  d       </xsl:text>
		</marc:controlfield>
		<marc:controlfield tag="007">cr</marc:controlfield>
		<marc:datafield tag="035" ind1=" " ind2=" ">
			<marc:subfield code="a"><xsl:value-of select="$localID"/></marc:subfield>
		</marc:datafield>
		<marc:datafield tag="099" ind1=" " ind2=" ">
			<marc:subfield code="a">
				<xsl:text>LD</xsl:text>
			</marc:subfield>
			<marc:subfield code="a">
				<xsl:if test="contains(/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact, 'Ph.')">791.9</xsl:if>
				<xsl:if test="contains(/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact, 'Ed.')">791.9</xsl:if>
				<xsl:if test="contains(/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact, 'M.')">791.8</xsl:if>
			</marc:subfield>
			<marc:subfield code="a">
				<xsl:text xml:space="preserve">.</xsl:text>
				<xsl:call-template name="processUCISubj">
					<xsl:with-param name="subj_area" select="$subjectArea"/>
				</xsl:call-template>
			</marc:subfield>
			<marc:subfield code="a">
				<xsl:value-of select="$date1"/>
			</marc:subfield>
		</marc:datafield>
		<xsl:for-each select="DISS_authorship/DISS_author">
			<xsl:if test="@type='primary'">
				<xsl:variable name="surname" select="DISS_name/DISS_surname" />
				<xsl:variable name="fname" select="DISS_name/DISS_fname" />
				<xsl:variable name="middle" select="DISS_name/DISS_middle" />
				<xsl:variable name="suffix" select="DISS_name/DISS_suffix" />
				<xsl:variable name="print_name">
					<xsl:value-of select="$surname" />, <xsl:value-of select="$fname" /><xsl:text> </xsl:text><xsl:value-of select="$middle" />
				</xsl:variable> 
				<xsl:call-template name="persname_template">
					<xsl:with-param name="string" select="normalize-space($print_name)" />
					<xsl:with-param name="suffix" select="$suffix"/>
					<xsl:with-param name="field" select="'100'" />
					<xsl:with-param name="ind1" select = "'1'" />
					<xsl:with-param name="ind2" select = "' '" />
					<xsl:with-param name="type" select="'author'" />
				</xsl:call-template>
			</xsl:if>
		</xsl:for-each>
		
		<xsl:variable name="nonFilingCharsInd">
			<xsl:call-template name="nonFilingChars">
				<xsl:with-param name="titlestr" select="DISS_description/DISS_title"/>
			</xsl:call-template>
		</xsl:variable>	
		<marc:datafield tag="245" ind1="1">
			<xsl:attribute name="ind2">
				<xsl:value-of select="$nonFilingCharsInd"/>
			</xsl:attribute>
			<xsl:choose>
				<xsl:when test="contains($etdTitle, ': ')">
					<marc:subfield code="a">
						<xsl:value-of select="concat(upper-case(substring($etdTitle, 1, 1)), lower-case(substring(substring-before($etdTitle, ': '), 2)))"/>
					</marc:subfield>
					<marc:subfield code="b">
						<xsl:value-of select="lower-case(substring-after($etdTitle, ': '))"/>
					</marc:subfield>
				</xsl:when>
				<xsl:otherwise>
					<marc:subfield code="a">
						<xsl:value-of select="concat(upper-case(substring($etdTitle, 1, 1)), lower-case(substring($etdTitle, 2)))"/>
					</marc:subfield>
				</xsl:otherwise>
			</xsl:choose>
			<marc:subfield code="c">/ by <xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_fname)!=0">
			<xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_fname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_middle)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_middle)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_surname)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_surname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_suffix)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_suffix)" />
			</xsl:if>.</marc:subfield>
		</marc:datafield>
		<marc:datafield tag="264" ind1=" " ind2="1">
			<marc:subfield code="a">Irvine, Calif. :</marc:subfield>
			<marc:subfield code="b">University of California, Irvine, </marc:subfield>
			<marc:subfield code="c">[<xsl:value-of select="$date1"/>]</marc:subfield>
		</marc:datafield>
		<xsl:if test="DISS_description">
			<marc:datafield tag="300" ind1=" " ind2=" ">
				<marc:subfield code="a">
					<xsl:text xml:space="preserve">1 online resource (</xsl:text>
					<xsl:value-of select="/DISS_submission/DISS_description/@page_count"/>
					<xsl:text xml:space="preserve"> pages)</xsl:text>
				</marc:subfield>
			</marc:datafield>
		</xsl:if>
		
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
		<marc:datafield tag="502" ind1=" " ind2=" ">
			<marc:subfield code="b"><xsl:value-of select="$degree"/></marc:subfield>
			<marc:subfield code="c">University of California, Irvine</marc:subfield>
			<marc:subfield code="d"><xsl:value-of select="$date1"/><xsl:text>.</xsl:text></marc:subfield>
		</marc:datafield>
		<marc:datafield tag="504" ind1=" " ind2=" ">
			<marc:subfield code="a">Includes bibliographical references.</marc:subfield>
		</marc:datafield>
		<xsl:if test="DISS_content/DISS_abstract/DISS_para">
			<xsl:variable name="Abstract">
				<xsl:for-each select="DISS_content/DISS_abstract/DISS_para">
					<xsl:value-of select="normalize-space(.)"/><xsl:text>&#160;</xsl:text>
				</xsl:for-each>
			</xsl:variable>
			<xsl:if test="string-length($Abstract)!=0">
				<marc:datafield tag="520" ind1="3" ind2=" ">
					<xsl:if test="string-length($Abstract)&lt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="$Abstract" />
						</marc:subfield>  
					</xsl:if>
		      		<xsl:if test="string-length($Abstract)&gt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="substring($Abstract, 1, 9980)" />...</marc:subfield>
					</xsl:if>
				</marc:datafield>
			</xsl:if>
		</xsl:if>
		
		<marc:datafield tag="588" ind1=" " ind2=" ">
			<marc:subfield code="a">
				<xsl:text xml:space="preserve">Description based on online resource; title from PDF title page (ProQuest, viewed )</xsl:text>
			</marc:subfield>
		</marc:datafield>
		<xsl:if test="string-length(//DISS_keyword)!=0">
			<xsl:for-each select="tokenize(//DISS_keyword, ', ')">
				<marc:datafield tag="653" ind1=" " ind2=" ">
					<marc:subfield code="a">
						<xsl:value-of select="."/>
					</marc:subfield>
				</marc:datafield>
			</xsl:for-each>
		</xsl:if>
		<marc:datafield tag="655" ind1=" " ind2="7">
			<marc:subfield code="a">Dissertations, Academic</marc:subfield>
			<marc:subfield code="z">University of California, Irvine</marc:subfield>
			<marc:subfield code="x"><xsl:value-of select="$subjectArea"/><xsl:text>.</xsl:text></marc:subfield> 
			<marc:subfield code="2">local</marc:subfield>
		</marc:datafield>
		<marc:datafield tag="793" ind1="0" ind2="8">
			<marc:subfield code="a">UCI electronic theses and dissertations</marc:subfield>
		</marc:datafield>
		<xsl:choose>
			<xsl:when test="@embargo_code=0">
				<marc:datafield tag="856" ind1="4" ind2="8">
					<marc:subfield code="z">Open Access via eScholarship</marc:subfield>
					<marc:subfield code="u"><xsl:call-template name="lookupEScholLink">
						<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>		
			</xsl:when>
			<xsl:otherwise>
				<marc:datafield tag="856" ind1="4" ind2="8">
					<marc:subfield code="z">Due to student requested embargo, full text not available until <xsl:call-template name="calculate_embargo_enddate">
							<xsl:with-param name="embargocode" select="@embargo_code"/>
							<xsl:with-param name="submit_date" select="$accept_date"/>
							<xsl:with-param name="embargo_code4" select="$embargo_end_date_string"/>
						</xsl:call-template>
					</marc:subfield>
					<marc:subfield code="u">
						<xsl:call-template name="lookupEScholLink">
							<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>
			</xsl:otherwise>
		</xsl:choose>
	</marc:record>		
</xsl:template>
<xsl:template name="ucla_template">
		<marc:record>
		<xsl:variable name="date1" select="normalize-space(DISS_description/DISS_dates/DISS_comp_date)" />
		<xsl:variable name="accept_date" select="normalize-space(DISS_description/DISS_dates/DISS_accept_date)"/>
		<!--Start by building the LDR, 007 and 008 -->
		<!--VESTIGIAL NOTE IN ORIGINAL STYLESHEET: Processing problem is somewhere within the leader or controlfield element-->
		<marc:leader>02211nam a2200289Ki 4500</marc:leader>
		<marc:controlfield tag="006">
			<xsl:text xml:space="preserve">m     o  d        </xsl:text>
		</marc:controlfield>
		<marc:controlfield tag="007"><xsl:text>cr |n|||||||||</xsl:text></marc:controlfield>
		  
		<marc:controlfield tag="008">
			<xsl:text>051012t</xsl:text>
			<xsl:value-of select="$date1" />
		    <xsl:value-of select="$date1" />
		    <xsl:text>cau     o     000 0 eng d</xsl:text>
		</marc:controlfield>
		<marc:datafield tag="035" ind1="9" ind2=" ">
			<marc:subfield code="9">(PQExtID)<xsl:value-of select="$localID"/></marc:subfield>
		</marc:datafield>
		<xsl:for-each select="DISS_authorship/DISS_author">
			<xsl:if test="@type='primary'">
				<xsl:variable name="surname" select="DISS_name/DISS_surname" />
				<xsl:variable name="fname" select="DISS_name/DISS_fname" />
				<xsl:variable name="middle" select="DISS_name/DISS_middle" />
				<xsl:variable name="suffix" select="DISS_name/DISS_suffix" />
				<xsl:variable name="print_name">
					<xsl:value-of select="$surname" />, <xsl:value-of select="$fname" /><xsl:text> </xsl:text><xsl:value-of select="$middle" />
				</xsl:variable> 
				<xsl:call-template name="persname_template">
					<xsl:with-param name="string" select="normalize-space($print_name)" />
					<xsl:with-param name="suffix" select="$suffix"/>
					<xsl:with-param name="field" select="'100'" />
					<xsl:with-param name="ind1" select = "'1'" />
					<xsl:with-param name="ind2" select = "' '" />
					<xsl:with-param name="type" select="'author'" />
				</xsl:call-template>
			</xsl:if>
		</xsl:for-each>
		
		<xsl:variable name="nonFilingCharsInd">
			<xsl:call-template name="nonFilingChars">
				<xsl:with-param name="titlestr" select="DISS_description/DISS_title"/>
			</xsl:call-template>
		</xsl:variable>	
		<marc:datafield>
			<xsl:attribute name="tag">
				<xsl:value-of select="245"/>
			</xsl:attribute>
			<xsl:attribute name="ind1">
				<xsl:value-of select="1"/>
			</xsl:attribute>
			<xsl:attribute name="ind2">
				<xsl:value-of select="$nonFilingCharsInd"/>
			</xsl:attribute>
			<marc:subfield code="a"><xsl:value-of select="normalize-space(DISS_description/DISS_title)" /> /</marc:subfield>
			<marc:subfield code="c">by <xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_fname)!=0">
			<xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_fname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_middle)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_middle)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_surname)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_surname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_suffix)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_suffix)" />
			</xsl:if>.</marc:subfield>
		</marc:datafield>

		<marc:datafield tag="264" ind1=" " ind2="1">
			<marc:subfield code="a">[Los Angeles, Calif.] : </marc:subfield>
			<marc:subfield code="b">University of California, Los Angeles, </marc:subfield>
			<marc:subfield code="c"><xsl:value-of select="$date1" />.</marc:subfield>
		</marc:datafield>
		
		<marc:datafield tag="264" ind1=" " ind2="4">
			<marc:subfield code="c">&#169;<xsl:value-of select="$date1" /></marc:subfield>
		</marc:datafield>

		<xsl:if test="DISS_description">
			<xsl:variable name="page" select="DISS_description/@page_count" />
			<marc:datafield tag="300" ind1=" " ind2=" ">
				<marc:subfield code="a">1 online resource (<xsl:value-of select="$page" /> pages)</marc:subfield>
			</marc:datafield>
		</xsl:if>
		<marc:datafield tag="336" ind1=" " ind2=" ">
			<marc:subfield code="a">text</marc:subfield>
			<marc:subfield code="b">txt</marc:subfield>
			<marc:subfield code="2">rdacontent</marc:subfield>
		</marc:datafield>
		  
		<marc:datafield tag="337" ind1=" " ind2=" ">
			<marc:subfield code="a">computer</marc:subfield>
			<marc:subfield code="b">c</marc:subfield>
			<marc:subfield code="2">rdamedia</marc:subfield>
		</marc:datafield>
		  
		<marc:datafield tag="338" ind1=" " ind2=" ">
			<marc:subfield code="a">online resource</marc:subfield>
			<marc:subfield code="b">cr</marc:subfield>
			<marc:subfield code="2">rdacarrier</marc:subfield>
		</marc:datafield>
		
		<xsl:if test="DISS_description/DISS_advisor">
			<xsl:for-each select="DISS_description/DISS_advisor">
				<marc:datafield tag="500" ind1=" " ind2=" ">
					<marc:subfield code="a"><xsl:if test="string-length(./DISS_name/DISS_fname)!=0">
					<xsl:value-of select="normalize-space(./DISS_name/DISS_fname)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_middle)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_middle)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_surname)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_surname)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_suffix)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_suffix)" />
				</xsl:if>, advisor.</marc:subfield>
				</marc:datafield>
			</xsl:for-each>
		</xsl:if>

<!--		<marc:datafield tag="588" ind1=" " ind2=" ">
			<xsl:variable name="dateToday" select="current-date()" />
			<marc:subfield code="a">Description based on information submitted by dissertant (created <xsl:value-of select="format-date($dateToday, '[MNn] [D], [Y]')"/>).</marc:subfield>		
		</marc:datafield>
-->
		<marc:datafield tag="502" ind1=" " ind2=" ">
			<xsl:variable name="degree" select="DISS_description/DISS_degree" />
		    <xsl:variable name="org" select="DISS_description/DISS_institution/DISS_inst_name" />
			<marc:subfield code="g">Thesis</marc:subfield>
			<marc:subfield code="b"><xsl:value-of select="$degree" /></marc:subfield>
			<marc:subfield code="c"><xsl:value-of select="$org" /></marc:subfield>
			<marc:subfield code="d"><xsl:value-of select="$date1" />.</marc:subfield>
		</marc:datafield>

<!-- Creates 506 for embargoed ETD based on embargo code; ETDs with embargo code 0 have no 506 field -->		
		<xsl:if test="@embargo_code!=0">
			<marc:datafield tag="506" ind1=" " ind2=" ">
				<marc:subfield code="a">Embargoed until <xsl:call-template name="calculate_embargo_enddate">
					<xsl:with-param name="embargocode" select="@embargo_code"/>
					<xsl:with-param name="submit_date" select="$accept_date"/>
					<xsl:with-param name="embargo_code4" select="$embargo_end_date_string"/>
				</xsl:call-template>.</marc:subfield>
			</marc:datafield>
		</xsl:if>

		<xsl:if test="DISS_content/DISS_abstract/DISS_para">
			<xsl:variable name="Abstract">
				<xsl:for-each select="DISS_content/DISS_abstract/DISS_para">
					<xsl:value-of select="normalize-space(.)"/><xsl:text>&#160;</xsl:text>
				</xsl:for-each>
			</xsl:variable>
			<xsl:if test="string-length($Abstract)!=0">
				<marc:datafield tag="520" ind1="3" ind2=" ">
					<xsl:if test="string-length($Abstract)&lt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="$Abstract" />
						</marc:subfield>  
					</xsl:if>
		      		<xsl:if test="string-length($Abstract)&gt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="substring($Abstract, 1, 9980)" />...</marc:subfield>
					</xsl:if>
				</marc:datafield>
			</xsl:if>
		</xsl:if>
		  
		<xsl:if test="string-length(//DISS_keyword)!=0">
			<marc:datafield tag="653" ind1=" " ind2=" ">
				<xsl:for-each select="tokenize(//DISS_keyword, ', ')">
					<marc:subfield code="a">
						<xsl:value-of select="."/>
					</marc:subfield>
				</xsl:for-each>
			</marc:datafield>
		</xsl:if>
		
		<xsl:for-each select="DISS_description/DISS_institution">
			<marc:datafield tag="655" ind1=" " ind2="7">
				<xsl:variable name="ucla_subj" select="DISS_inst_contact"/>
				<marc:subfield code="a">Dissertations, Academic</marc:subfield>
				<marc:subfield code="z">UCLA</marc:subfield>
<!--DISS_inst_contact field ends with a 4-digit code that we want to exclude -->
				<marc:subfield code="x"><xsl:value-of select="substring($ucla_subj, 1, string-length($ucla_subj) - 5)" />.</marc:subfield>
				<marc:subfield code="2">local</marc:subfield>
			</marc:datafield>  
		</xsl:for-each>

		<marc:datafield tag="793" ind1="0" ind2=" ">
			<marc:subfield code="a">UCLA online theses and dissertations.</marc:subfield>
		</marc:datafield>  
		  
		<xsl:for-each select="DISS_authorship/DISS_author">
			<xsl:if test="@type!='primary'">
				<xsl:variable name="surname" select="DISS_name/DISS_surname" />
				<xsl:variable name="fname" select="DISS_name/DISS_fname" />
				<xsl:variable name="middle" select="DISS_name/DISS_middle" />
				<xsl:variable name="suffix" select="DISS_name/DISS_suffix" />
				<xsl:variable name="print_name">
					<xsl:value-of select="$surname" /> <xsl:value-of select="$suffix" />, <xsl:value-of select="$fname" /><xsl:text> </xsl:text><xsl:value-of select="$middle" />
				</xsl:variable>
				<xsl:call-template name="persname_template">
					<xsl:with-param name="string" select="normalize-space($print_name)" />
					<xsl:with-param name="suffix" select="$suffix"/>
					<xsl:with-param name="field" select="'700'" />
					<xsl:with-param name="ind1" select = "'1'" />
					<xsl:with-param name="ind2" select = "' '" />
					<xsl:with-param name="type" select="'author'" />
				</xsl:call-template>
			</xsl:if>
		</xsl:for-each>

		<xsl:choose>
			<xsl:when test="@embargo_code=0">
				<marc:datafield tag="856" ind1="4" ind2="0">
					<marc:subfield code="z">Open Access via eScholarship</marc:subfield>
					<marc:subfield code="u"><xsl:call-template name="lookupEScholLink">
						<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>		
			</xsl:when>
			<xsl:otherwise>
				<marc:datafield tag="856" ind1="4" ind2="0">
					<marc:subfield code="z">eScholarship. Embargoed until <xsl:call-template name="calculate_embargo_enddate">
							<xsl:with-param name="embargocode" select="@embargo_code"/>
							<xsl:with-param name="submit_date" select="$accept_date"/>
							<xsl:with-param name="embargo_code4" select="$embargo_end_date_string"/>
						</xsl:call-template>
					</marc:subfield>
					<marc:subfield code="u">
						<xsl:call-template name="lookupEScholLink">
							<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>
			</xsl:otherwise>
		</xsl:choose>
		</marc:record>		
</xsl:template>

<xsl:template name="ucsd_template">
	<marc:record>
		<xsl:variable name="date1" select="normalize-space(DISS_description/DISS_dates/DISS_comp_date)" />
		<xsl:variable name="accept_date" select="normalize-space(DISS_description/DISS_dates/DISS_accept_date)"/>
		<!--Start by building the LDR, 007 and 008 -->
		<!--VESTIGIAL NOTE IN ORIGINAL STYLESHEET: Processing problem is somewhere within the leader or controlfield element-->
		<marc:leader>02211nam a2200289Ki 4500</marc:leader>
		<marc:controlfield tag="006">
			<xsl:text xml:space="preserve">m     o  d        </xsl:text>
		</marc:controlfield>
		<marc:controlfield tag="007"><xsl:text>cr |n|||||||||</xsl:text></marc:controlfield>
		  
		<marc:controlfield tag="008">
			<xsl:text>051012t</xsl:text>
			<xsl:value-of select="$date1" />
		    <xsl:value-of select="$date1" />
		    <xsl:text>cau     o     000 0 eng d</xsl:text>
		</marc:controlfield>
		  
		<xsl:for-each select="DISS_authorship/DISS_author">
			<xsl:if test="@type='primary'">
				<xsl:variable name="surname" select="DISS_name/DISS_surname" />
				<xsl:variable name="fname" select="DISS_name/DISS_fname" />
				<xsl:variable name="middle" select="DISS_name/DISS_middle" />
				<xsl:variable name="suffix" select="DISS_name/DISS_suffix" />
				<xsl:variable name="print_name">
					<xsl:value-of select="$surname" />, <xsl:value-of select="$fname" /><xsl:text> </xsl:text><xsl:value-of select="$middle" />
				</xsl:variable> 
				<xsl:call-template name="persname_template">
					<xsl:with-param name="string" select="normalize-space($print_name)" />
					<xsl:with-param name="suffix" select="$suffix"/>
					<xsl:with-param name="field" select="'100'" />
					<xsl:with-param name="ind1" select = "'1'" />
					<xsl:with-param name="ind2" select = "' '" />
					<xsl:with-param name="type" select="'author'" />
				</xsl:call-template>
			</xsl:if>
		</xsl:for-each>

		<xsl:variable name="nonFilingCharsInd">
			<xsl:call-template name="nonFilingChars">
				<xsl:with-param name="titlestr" select="DISS_description/DISS_title"/>
			</xsl:call-template>
		</xsl:variable>	
		<marc:datafield>
			<xsl:attribute name="tag">
				<xsl:value-of select="245"/>
			</xsl:attribute>
			<xsl:attribute name="ind1">
				<xsl:value-of select="1"/>
			</xsl:attribute>
			<xsl:attribute name="ind2">
				<xsl:value-of select="$nonFilingCharsInd"/>
			</xsl:attribute>
			<marc:subfield code="a"><xsl:value-of select="normalize-space(DISS_description/DISS_title)" /> /</marc:subfield>
			<marc:subfield code="c">by <xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_fname)!=0">
			<xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_fname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_middle)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_middle)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_surname)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_surname)" />
			</xsl:if><xsl:if test="string-length(//DISS_authorship/DISS_author/DISS_name/DISS_suffix)!=0">
				<xsl:text> </xsl:text><xsl:value-of select="normalize-space(DISS_authorship/DISS_author/DISS_name/DISS_suffix)" />
			</xsl:if>.</marc:subfield>
		</marc:datafield>

		<marc:datafield tag="264" ind1=" " ind2="1">
			<marc:subfield code="a">[La Jolla, Calif.] : </marc:subfield>
			<marc:subfield code="b">University of California, San Diego, </marc:subfield>
			<marc:subfield code="c"><xsl:value-of select="$date1" />.</marc:subfield>
		</marc:datafield>
		
		<marc:datafield tag="264" ind1=" " ind2="4">
			<marc:subfield code="c">&#169;<xsl:value-of select="$date1" /></marc:subfield>
		</marc:datafield>

		<xsl:if test="DISS_description">
			<xsl:variable name="page" select="DISS_description/@page_count" />
			<marc:datafield tag="300" ind1=" " ind2=" ">
				<marc:subfield code="a">1 online resource (<xsl:value-of select="$page" /> pages)</marc:subfield>
			</marc:datafield>
		</xsl:if>
		<marc:datafield tag="336" ind1=" " ind2=" ">
			<marc:subfield code="a">text</marc:subfield>
			<marc:subfield code="b">txt</marc:subfield>
			<marc:subfield code="2">rdacontent</marc:subfield>
		</marc:datafield>
		  
		<marc:datafield tag="337" ind1=" " ind2=" ">
			<marc:subfield code="a">computer</marc:subfield>
			<marc:subfield code="b">c</marc:subfield>
			<marc:subfield code="2">rdamedia</marc:subfield>
		</marc:datafield>
		  
		<marc:datafield tag="338" ind1=" " ind2=" ">
			<marc:subfield code="a">online resource</marc:subfield>
			<marc:subfield code="b">cr</marc:subfield>
			<marc:subfield code="2">rdacarrier</marc:subfield>
		</marc:datafield>
		
		<xsl:if test="DISS_description/DISS_advisor">
			<xsl:for-each select="DISS_description/DISS_advisor">
				<marc:datafield tag="500" ind1=" " ind2=" ">
					<marc:subfield code="a"><xsl:if test="string-length(./DISS_name/DISS_fname)!=0">
					<xsl:value-of select="normalize-space(./DISS_name/DISS_fname)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_middle)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_middle)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_surname)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_surname)" />
				</xsl:if><xsl:if test="string-length(./DISS_name/DISS_suffix)!=0">
					<xsl:text> </xsl:text><xsl:value-of select="normalize-space(./DISS_name/DISS_suffix)" />
				</xsl:if>, advisor.</marc:subfield>
				</marc:datafield>
			</xsl:for-each>
		</xsl:if>

		<marc:datafield tag="588" ind1=" " ind2=" ">
			<xsl:variable name="dateToday" select="current-date()" />
			<marc:subfield code="a">Description based on information submitted by author (created <xsl:value-of select="format-date($dateToday, '[MNn] [D], [Y]')"/>).</marc:subfield>		
		</marc:datafield>

		<marc:datafield tag="502" ind1=" " ind2=" ">
			<xsl:variable name="degree" select="DISS_description/DISS_degree" />
		    <xsl:variable name="org" select="DISS_description/DISS_institution/DISS_inst_name" />
			<marc:subfield code="g">Thesis</marc:subfield>
			<marc:subfield code="b"><xsl:value-of select="$degree" /></marc:subfield>
			<marc:subfield code="c"><xsl:value-of select="$org" /></marc:subfield>
			<marc:subfield code="d"><xsl:value-of select="$date1" />.</marc:subfield>
		</marc:datafield>

<!-- Creates 506 for embargoed ETD based on embargo code; ETDs with embargo code 0 have no 506 field -->		
		<xsl:if test="@embargo_code!=0">
			<marc:datafield tag="506" ind1=" " ind2=" ">
				<marc:subfield code="a">Embargoed until <xsl:call-template name="calculate_embargo_enddate">
					<xsl:with-param name="embargocode" select="@embargo_code"/>
					<xsl:with-param name="submit_date" select="$accept_date"/>
					<xsl:with-param name="embargo_code4" select="$embargo_end_date_string"/>
				</xsl:call-template>.</marc:subfield>
			</marc:datafield>
		</xsl:if>

		<xsl:if test="DISS_content/DISS_abstract/DISS_para">
			<xsl:variable name="Abstract">
				<xsl:for-each select="DISS_content/DISS_abstract/DISS_para">
					<xsl:value-of select="normalize-space(.)"/><xsl:text>&#160;</xsl:text>
				</xsl:for-each>
			</xsl:variable>
			<xsl:if test="string-length($Abstract)!=0">
				<marc:datafield tag="520" ind1="3" ind2=" ">
					<xsl:if test="string-length($Abstract)&lt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="$Abstract" />
						</marc:subfield>  
					</xsl:if>
		      		<xsl:if test="string-length($Abstract)&gt;9980">
						<marc:subfield code="a">
							<xsl:value-of select="substring($Abstract, 1, 9980)" />...</marc:subfield>
					</xsl:if>
				</marc:datafield>
			</xsl:if>
		</xsl:if>
		  
		<xsl:if test="string-length(//DISS_keyword)!=0">
			<marc:datafield tag="653" ind1=" " ind2=" ">
				<xsl:for-each select="tokenize(//DISS_keyword, ', ')">
					<marc:subfield code="a">
						<xsl:value-of select="."/>
					</marc:subfield>
				</xsl:for-each>
			</marc:datafield>
		</xsl:if>
		<!-- UCSD uses alternate below, which provides department instead of category description for degree. -->
		<xsl:for-each select="DISS_description/DISS_institution">
			<marc:datafield tag="655" ind1=" " ind2="7">
				<marc:subfield code="a">Dissertations, Academic</marc:subfield>
				<marc:subfield code="z">UCSD</marc:subfield>
				<marc:subfield code="x"><xsl:value-of select="DISS_inst_contact" />.</marc:subfield>
				<marc:subfield code="2">local</marc:subfield>
			</marc:datafield>  
		</xsl:for-each>

		<marc:datafield tag="793" ind1="0" ind2=" ">
			<marc:subfield code="a">UCSD online theses and dissertations.</marc:subfield>
		</marc:datafield> 
		<marc:datafield tag="793" ind1="0" ind2=" ">
			<marc:subfield code="a">Open access resource; selected by the UC San Diego Library.</marc:subfield>
			<marc:subfield code="p">eScholarship online dissertations</marc:subfield>
		</marc:datafield>

		<xsl:for-each select="DISS_authorship/DISS_author">
			<xsl:if test="@type!='primary'">
				<xsl:variable name="surname" select="DISS_name/DISS_surname" />
				<xsl:variable name="fname" select="DISS_name/DISS_fname" />
				<xsl:variable name="middle" select="DISS_name/DISS_middle" />
				<xsl:variable name="suffix" select="DISS_name/DISS_suffix" />
				<xsl:variable name="print_name">
					<xsl:value-of select="$surname" /> <xsl:value-of select="$suffix" />, <xsl:value-of select="$fname" /><xsl:text> </xsl:text><xsl:value-of select="$middle" />
				</xsl:variable>
				<xsl:call-template name="persname_template">
					<xsl:with-param name="string" select="normalize-space($print_name)" />
					<xsl:with-param name="suffix" select="$suffix"/>
					<xsl:with-param name="field" select="'700'" />
					<xsl:with-param name="ind1" select = "'1'" />
					<xsl:with-param name="ind2" select = "' '" />
					<xsl:with-param name="type" select="'author'" />
				</xsl:call-template>
			</xsl:if>
		</xsl:for-each>
		
		<xsl:choose>
			<xsl:when test="@embargo_code=0">
				<marc:datafield tag="856" ind1="4" ind2="0">
					<marc:subfield code="z">Open Access via eScholarship</marc:subfield>
					<marc:subfield code="u"><xsl:call-template name="lookupEScholLink">
						<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>		
			</xsl:when>
			<xsl:otherwise>
				<marc:datafield tag="856" ind1="4" ind2="0">
					<marc:subfield code="z">eScholarship. Embargoed until <xsl:call-template name="calculate_embargo_enddate">
							<xsl:with-param name="embargocode" select="@embargo_code"/>
							<xsl:with-param name="submit_date" select="$accept_date"/>
							<xsl:with-param name="embargo_code4" select="$embargo_end_date_string"/>
						</xsl:call-template>
					</marc:subfield>
					<marc:subfield code="u">
						<xsl:call-template name="lookupEScholLink">
							<xsl:with-param name="local_id" select="substring-after(//DISS_description/@external_id, 'http://dissertations.umi.com/')"/>
						</xsl:call-template>
					</marc:subfield>
				</marc:datafield>
			</xsl:otherwise>
		</xsl:choose>
	</marc:record>		
</xsl:template>
<xsl:template name="exception_template">

<xsl:result-document method="text" href="/home/uc3/etds/marc/etd{$localID}.txt">
	<xsl:value-of select="$campus_code"/>
	<xsl:text>&#x9;</xsl:text>
	<xsl:value-of select="$localID"/>
	<xsl:text>&#xA;</xsl:text>
</xsl:result-document>
</xsl:template>

<xsl:template name="persname_template">
	<xsl:param name="string" />
	<xsl:param name="suffix"/>
	<xsl:param name="field" />
	<xsl:param name="ind1" />
	<xsl:param name="ind2" />
	<xsl:param name="type" />
	<marc:datafield>
		<xsl:attribute name="tag">
			<xsl:value-of select="$field" />
		</xsl:attribute>
		<xsl:attribute name="ind1">
			<xsl:value-of select="$ind1" />
		</xsl:attribute>
		<xsl:attribute name="ind2">
			<xsl:value-of select="$ind2" />
		</xsl:attribute>
		<xsl:choose>
			<xsl:when test="$suffix!=''">
				<marc:subfield code="a">
					<xsl:value-of select="$string" />
				</marc:subfield>
				<marc:subfield code="c">
					<xsl:text> </xsl:text>
					<xsl:value-of select="$suffix"/>
					<xsl:text>, </xsl:text>
				</marc:subfield>
			</xsl:when>
			<xsl:otherwise>
				<marc:subfield code="a">
					<xsl:value-of select="$string" />
					<xsl:text>, </xsl:text>
				</marc:subfield>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:if test="contains($string, '(')">
			<xsl:variable name="subq_tmp" select="substring-after($string, '(')" />
			<xsl:variable name="subq" select="substring-before($subq_tmp, ')')" />
			<marc:subfield code="q">
				(<xsl:value-of select="$subq" />)
			</marc:subfield>
		</xsl:if>
		<marc:subfield code="e"><xsl:value-of select="$type" />.</marc:subfield>
	</marc:datafield>
</xsl:template>
	
<xsl:template name="lookupEScholLink">
	<xsl:param name="local_id" />
	<xsl:variable name="merritt_local_id" select="concat('PQETD:',substring-before($local_id,':'),substring-after($local_id,':'))"/>
	<xsl:choose>
		<xsl:when test="string-length($lookupID/key('local_id',$merritt_local_id)/value[@column = '2'])!=0">
			<xsl:value-of select="$lookupID/key('local_id',$merritt_local_id)/value[@column = '2']"/>
		</xsl:when>
		<xsl:otherwise>ERROR: <xsl:value-of select="$merritt_local_id"/></xsl:otherwise>
	</xsl:choose>
</xsl:template>	

<xsl:template name="nonFilingChars">
	<xsl:param name="titlestr" />
	<xsl:choose>
		<xsl:when test="lower-case(substring($titlestr,1,2))='a '">
			<xsl:value-of select="2"/>
		</xsl:when>
		<xsl:when test="lower-case(substring($titlestr,1,3))='an '">
			<xsl:value-of select="3"/>
		</xsl:when>
		<xsl:when test="lower-case(substring($titlestr,1,4))='the '">
			<xsl:value-of select="4"/>
		</xsl:when>
		<xsl:otherwise>
			<xsl:value-of select="0"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<xsl:template name="calculate_embargo_enddate">
	<xsl:param name="embargocode"/>
	<xsl:param name="submit_date"/>
	<xsl:param name="embargo_code4"/>
	<xsl:variable name="embargo_days">
		<xsl:choose>
			<xsl:when test="$embargocode=1">
				<xsl:value-of select="550"/>
			</xsl:when>
			<xsl:when test="$embargocode=2">
				<xsl:value-of select="730"/>
			</xsl:when>
			<xsl:when test="$embargocode=3">
				<xsl:value-of select="1095"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="0"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:variable>
	<xsl:choose>
		<xsl:when test="$embargocode=4">
			<xsl:value-of select="$embargo_code4"/>
		</xsl:when>
		<xsl:otherwise>
			<xsl:variable name="ISOdatestring">
				<xsl:value-of select="concat(substring($submit_date,7,4),'-',substring($submit_date,1,2),'-',substring($submit_date,4,2))"/> 
			</xsl:variable>
			<xsl:variable name="formatted_date" as="xs:date" select="xs:date($ISOdatestring)"/>
			<xsl:variable name="embargo_end_date_formatted" select="$formatted_date + $embargo_days*xs:dayTimeDuration('P1D')"/>
			<xsl:value-of select="format-date($embargo_end_date_formatted, '[M01]/[D01]/[Y0001]')"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>
<xsl:template name="processUCISubj">
        <xsl:param name="subj_area" />
        <xsl:variable name="subjString01" select="substring-before( concat( $subj_area, '-' ) , '-' )"/>
        <xsl:variable name="subjString02" select="substring-before( concat( $subjString01, 'with'), 'with')"/>
        <xsl:call-template name="lookupUCISubj">
            <xsl:with-param name="subjectString" select="replace($subjString02, '\s+$', '')"/>
        </xsl:call-template>
</xsl:template>
<xsl:template name="lookupUCISubj">
	<xsl:param name="subjectString" />
	<xsl:choose>
		<xsl:when test="string-length($lookupSubj/table/rows/row/value[text()=$subjectString])!=0">
			<xsl:value-of select="$lookupSubj/table/rows/row/value[text()=$subjectString]/../value[@column='1']"/>
		</xsl:when>
		<xsl:otherwise>ERROR: <xsl:value-of select="$subjectString"/></xsl:otherwise>
	</xsl:choose>
</xsl:template>	
<xsl:template name="calculate_lang_code">
	<xsl:param name="PQ_lang_code"/>
	<xsl:if test="lower-case($PQ_lang_code)='en'">eng</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='af'">afr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='as'">afr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='an'">ang</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ar'">ara</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ae'">ara</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ah'">ara</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='bq'">baq</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ca'">cat</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ch'">chi</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ce'">chi</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='cr'">hrv</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='cz'">cze</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='da'">dan</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='du'">dum</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='de'">dum</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='dl'">dum</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='es'">est</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ef'">est</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ez'">est</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fi'">fin</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fn'">fin</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fl'">dut</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fr'">fre</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fe'">fre</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='fs'">fre</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ga'">glg</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ge'">ger</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='gn'">ger</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='gr'">gre</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='hi'">haw</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='hn'">haw</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='he'">heb</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='hg'">heb</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='hy'">heb</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='hu'">hun</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='eh'">hun</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ic'">ice</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ir'">gle</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='it'">ita</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ie'">ita</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ja'">eng</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='je'">jpn</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='jp'">jpr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ko'">kor</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ke'">kor</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='la'">lat</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='el'">lat</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='lv'">lav</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='li'">lit</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='me'">enm</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='no'">nor</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ne'">nor</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='pn'">per</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='pl'">pol</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ph'">pol</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='pr'">por</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='pe'">por</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ro'">rum</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ru'">rus</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='re'">rus</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sa'">san</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sd'">nso</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='so'">sot</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sp'">spa</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sr'">spa</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sb'">spa</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='se'">spa</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sl'">spa</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sw'">swe</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='sg'">swe</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ss'">syr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='te'">tha</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='to'">nai</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ts'">ven</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='tu'">tur</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='tw'">tsn</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='uk'">ukr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='ue'">ukr</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='we'">wel</xsl:if>
	<xsl:if test="lower-case($PQ_lang_code)='yi'">yid</xsl:if>
</xsl:template>
</xsl:stylesheet>
