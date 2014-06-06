<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Monitor Tasks - CSV Import Stylesheet

         CSV fields:
         Host....................monitor_task.host_id$name
         Check...................monitor_task.check_id$name
         Enabled.................monitor_task.enabled
         Comments................monitor_task.comments
         Option:XX...............Option,Value (Option = XX in column name, value = cell in row)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="CheckPrefix" select="'Check:'"/>
    <xsl:variable name="HostPrefix" select="'Host:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="check" match="row" use="col[@field='Check']"/>
    <xsl:key name="host" match="row" use="col[@field='Host']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Checks -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('check',
                                                                       col[@field='Check'])[1])]">
                <xsl:call-template name="Check" />
            </xsl:for-each>

            <!-- Hosts -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('host',
                                                                       col[@field='Host'])[1])]">
                <xsl:call-template name="Host" />
            </xsl:for-each>

            <!-- Tasks -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Enabled">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Enabled']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <!-- Task -->
        <resource name="monitor_task">
            <xsl:choose>
                <xsl:when test="$Enabled=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Enabled='Y'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='YES'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='T'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='TRUE'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='N'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='NO'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='F'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='FALSE'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
            </xsl:choose>

            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <!-- Link to Check -->
            <reference field="check_id" resource="monitor_check">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($CheckPrefix, col[@field='Check'])"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Host -->
            <reference field="host_id" resource="monitor_host">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($HostPrefix, col[@field='Host'])"/>
                </xsl:attribute>
            </reference>

            <!-- Options -->
            <xsl:for-each select="col[starts-with(@field, 'Option')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Check">
        <xsl:variable name="CheckName">
            <xsl:value-of select="col[@field='Check']"/>
        </xsl:variable>

        <resource name="monitor_check">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($CheckPrefix, $CheckName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CheckName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Host">
        <xsl:variable name="HostName">
            <xsl:value-of select="col[@field='Host']"/>
        </xsl:variable>

        <resource name="monitor_host">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($HostPrefix, $HostName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$HostName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <!-- Skip empty values, even though these could be useful, otherwise we can't add add tasks for different checks from the same file -->
        <xsl:if test="$Value!=''">
            <resource name="monitor_task_option">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
