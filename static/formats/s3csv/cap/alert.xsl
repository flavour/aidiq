<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         CAP template - CSV Import Stylesheet

         CSV column..................Format.............Content

         Template Title..............string.............CAP template template_title
         Identifier..................string.............CAP template identifier
         Scope.......................string.............CAP template scope
         Restriction.................string.............CAP template restriction
         Recipients..................list:string........CAP template recipients (addresses)
         Note........................string.............CAP template note
         Incidents...................list:string........CAP template incidents
         Approved....................optional...........cap_alert.approved_by
                                                        Set to 'false' to not approve records.
                                                        Note this only works for prepop or users with acl.APPROVE rights

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>    
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
    
        <xsl:variable name="is_template">
            <xsl:text>true</xsl:text>
        </xsl:variable>
        
        <xsl:variable name="approved">
            <xsl:choose>
                <xsl:when test="col[@field='Approved']='false'">
                    <xsl:text>false</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>true</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <resource name="cap_alert">
            <xsl:attribute name="uuid">
                <xsl:value-of select="concat('urn:capid:', col[@field='Identifier']/text())"/>
            </xsl:attribute>
            <xsl:attribute name="approved">
                <xsl:value-of select="$approved"/>
            </xsl:attribute>
            <!-- Used for CAP Template -->
            <data field="is_template">
                <xsl:attribute name="value">
                    <xsl:value-of select="$is_template"/>
                </xsl:attribute>
            </data>
            <data field="template_title">
                <xsl:value-of select="col[@field='Template Title']"/>
            </data>
            <data field="template_settings">{}</data>
            <!-- Scope -->
            <xsl:variable name="Scope" select="col[@field='Scope']"/>
            <xsl:if test="$Scope!=''">
                <data field="scope">
                    <xsl:attribute name="value">
                        <xsl:value-of select="$Scope"/>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Restriction -->
            <xsl:variable name="Restriction" select="col[@field='Restriction']"/>
            <xsl:if test="$Restriction!='' and $Scope='Restricted'">
                <data field="restriction">
                    <xsl:value-of select="$Restriction"/>
                </data>
            </xsl:if>
            <!-- Recipients -->
            <xsl:variable name="list-recipients" select="col[@field='Recipients']"/>
            <xsl:variable name="list-recipients-val">
                <xsl:value-of select="substring-before(substring-after($list-recipients, '['), ']')"/>
            </xsl:variable>
            <xsl:if test="$list-recipients-val!=''">
                <data field="addresses">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:call-template name="list-String">
                            <xsl:with-param name="list">
                                <xsl:value-of select="$list-recipients-val"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Note -->
            <xsl:variable name="Note" select="col[@field='Note']"/>
            <xsl:if test="$Note!=''">
                <data field="note">
                    <xsl:value-of select="$Note"/>
                </data>
            </xsl:if>
            <!-- Incidents -->
            <xsl:variable name="list-incidents" select="col[@field='Incidents']"/>
            <xsl:variable name="list-incidents-val">
                <xsl:value-of select="substring-before(substring-after($list-incidents, '['), ']')"/>
            </xsl:variable>
            <xsl:if test="$list-incidents-val!=''">
                <data field="incidents">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:call-template name="list-String">
                            <xsl:with-param name="list">
                                <xsl:value-of select="$list-incidents-val"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>

        </resource>
    
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template name="list-String">

        <xsl:param name="list"/>
        <xsl:param name="listsep" select="','"/>

        <xsl:if test="$listsep">
            <xsl:choose>
                <xsl:when test="contains($list, $listsep)">
                    <xsl:variable name="head">
                        <xsl:value-of select="substring-before($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:text>"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($head, '&quot;', ''))"/>
                    <xsl:text>",</xsl:text>
                    <xsl:call-template name="list-String">
                        <xsl:with-param name="list" select="$tail"/>
                        <xsl:with-param name="listsep" select="$listsep"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="normalize-space($list)!=''">
                        <xsl:text>"</xsl:text>
                        <xsl:value-of select="normalize-space(translate($list, '&quot;', ''))"/>
                        <xsl:text>"</xsl:text>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>
    
</xsl:stylesheet>
