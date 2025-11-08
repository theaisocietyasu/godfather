import NextAuth from "next-auth";
import DiscordProvider from "next-auth/providers/discord";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: "identify email guilds guilds.members.read",
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // Store Discord info in JWT token
      if (account && profile) {
        token.discordId = (profile as any).id;
        token.discordUsername = (profile as any).username;
        token.discordAvatar = (profile as any).avatar;
      }
      return token;
    },
    async session({ session, token }) {
      // Make Discord info available in session
      if (session.user && token.discordId) {
        session.user.discordId = token.discordId;
        session.user.discordUsername = token.discordUsername || "";
        session.user.discordAvatar = token.discordAvatar || "";
      }
      return session;
    },
  },
  pages: {
    signIn: "/",
  },
});
